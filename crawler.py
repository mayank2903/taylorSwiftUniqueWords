import os.path
import re
import matplotlib.pyplot as plt
import argparse
import nltk
import requests
from bs4 import BeautifulSoup
import time
import random
from collections import defaultdict
import csv
from nltk.corpus import stopwords
import contractions

URL_FORMAT = "https://www.azlyrics.com/%s/%s.html"
PARENT_URL = "https://www.azlyrics.com"
PARENT_DIR_FORMAT = "word_frequencies/%s/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36,gzip(gfe)"}


class LyricsCrawler:

    def __init__(self, artist_name):
        self.artist_name = artist_name

        self.url = URL_FORMAT % (self.artist_name[0], self.artist_name)
        print('URL:', self.url)

        self.artist_dir = PARENT_DIR_FORMAT % self.artist_name
        print('PARENT_DIR:', self.artist_dir)

    def get_all_song_lyrics_urls(self, all_songs_page_url):
        r = requests.get(all_songs_page_url, headers=HEADERS)
        soup = BeautifulSoup(r.content, 'html5lib')
        song_urls = soup.findAll('div', {'class': 'listalbum-item'})
        canonicalized_urls = []
        for song_url in song_urls:
            if "google.com" not in song_url.a['href']:
                canonicalized_url = self.canonicalize_url(song_url.a['href'])
                canonicalized_urls.append(canonicalized_url)
            else:
                print('Ignoring url:', song_url.a['href'])
        return canonicalized_urls

    def canonicalize_url(self, relative_path):
        if relative_path.startswith(PARENT_URL):
            return relative_path
        else:
            return PARENT_URL + relative_path

    def get_word_list_for_song(self, url, stop_words):
        r = requests.get(url=url, headers=HEADERS)
        time.sleep(random.randint(30, 40))
        soup = BeautifulSoup(r.content, 'html.parser')
        # Find section which has song lyrics.
        lyrics = soup.find_all(lambda tag: tag.name == 'div' and not tag.attrs)[0].text
        symbols = "!@#$%^&*()_-+={[}]|\;:\"<>?/., "
        non_sanitized_words = lyrics.lower().split()
        sanitized_words = []
        for word in non_sanitized_words:
            # Remove most special symbols
            for i in range(len(symbols)):
                word = word.replace(symbols[i], '')
            # Expand contractions like "i'm", "i'll", so that they can also be removed using stopwords.
            expanded_words = contractions.fix(word).split()
            for word in expanded_words:
                if word not in stop_words:
                    sanitized_words.append(word)
        return sanitized_words

    def generate_dict(self, word_list):
        word_freq = {}
        word_freq = defaultdict(lambda: 0, word_freq)

        for word in word_list:
            word_freq[word] += 1
        return word_freq

    def export_per_song_word_freq(self, url, word_list):
        song_name = self.get_song_name(url)
        print(f"Exporting metrics of song: {song_name}")
        word_freq = self.generate_dict(word_list)

        file_name = self.artist_dir + song_name + ".csv"
        self.export_dict_to_csv_and_plot(file_name, word_freq)

    def get_song_name(self, url):
        url = url.removesuffix(".html")
        prefix_regex = "https://.*/"
        return re.sub(f"^({prefix_regex})", "", url)

    def export_all_songs_word_freq(self, all_song_words_list):
        word_freq = self.generate_dict(all_song_words_list)
        file_name = self.artist_dir + "all_song_freq.csv"
        self.export_dict_to_csv_and_plot(file_name, word_freq)

    def export_dict_to_csv_and_plot(self, file_name, word_freq):
        # Sort word frequencies in descending order.
        word_freq = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))

        # First ensure directory exists
        if not os.path.exists(self.artist_dir):
            os.makedirs(self.artist_dir)

        # Populate the file.
        try:
            with open(file_name, 'w') as csv_file:
                writer = csv.writer(csv_file)
                for key, value in word_freq.items():
                    writer.writerow([key, value])
            csv_file.close()
        except OSError:
            pass

        # Make the file read-only.
        os.chmod(file_name, 0o444)

        # Plot the top 50 words.
        self.plot_top_fifty_used_words(list(word_freq.items())[:50])

    def plot_top_fifty_used_words(self, word_freq):
        for x, y in word_freq:
            plt.bar(x, y, color='g', width=0.72)
            plt.xticks(rotation=90)
            plt.xlabel('Word', fontweight='bold')
            plt.ylabel('Frequency', fontweight='bold')
            plt.title('Top 50 Words Across All Songs - %s ' % self.artist_name)
        plt.show()

    def get_possibly_recorded_song_word_list(self, url):
        song_file = self.artist_dir + self.get_song_name(url) + ".csv"

        word_list = []
        try:
            if os.path.exists(song_file):
                print(f"{song_file} already exported. Skipping..")
                with open(song_file, 'r') as song_csv:
                    reader = csv.reader(song_csv)
                    for row in reader:
                        word = row[0]
                        count = int(row[1])
                        word_list = word_list + ([word] * count)
                    song_csv.close()
        except FileNotFoundError:
            pass
        return word_list

    def crawl(self):
        song_lyrics_page_urls = self.get_all_song_lyrics_urls(self.url)
        number_of_songs = len(song_lyrics_page_urls)
        print(f"{number_of_songs} songs found")

        # Sorting links by the song names. Helps track how far we are in crawling.
        song_lyrics_page_urls = sorted(song_lyrics_page_urls, reverse=True)

        # Collect all words of all songs by the artist.
        all_song_words = []
        i = 0
        nltk.download('stopwords')
        stop_words = set(stopwords.words('english'))
        for song_lyrics_page_url in song_lyrics_page_urls:
            i += 1
            print(f"[{i}/{number_of_songs}] Getting lyrics for: ", song_lyrics_page_url)

            # Check if metrics for this song already exported.
            word_list = self.get_possibly_recorded_song_word_list(song_lyrics_page_url)

            # If nothing recorded yet, crawl through lyrics page.
            if len(word_list) == 0:
                # Get and export per-song stats
                word_list = self.get_word_list_for_song(song_lyrics_page_url, stop_words)
                self.export_per_song_word_freq(song_lyrics_page_url, word_list)

            # Add result to all song words list.
            all_song_words = all_song_words + word_list

        # Export all songs' collective stats, provided we managed to crawl over all songs.
        if i == number_of_songs != 0:
            print('Exporting all song frequencies...')
            self.export_all_songs_word_freq(all_song_words)


if __name__ == "__main__":
    # Define cmdline flag for artist name.
    parser = argparse.ArgumentParser(description='Process lyrics of given artist')
    parser.add_argument('-a', '--artist', help='Artist name whose lyrics to process')
    args = parser.parse_args()
    if not args.artist:
        print('No artist name provided')
    else:
        # Instantiate crawler with cmdline flags, and run
        artist_name = str(args.artist).lower().replace(" ", "")
        print('Artist name:', artist_name)
        crawler = LyricsCrawler(artist_name=artist_name)
        crawler.crawl()
