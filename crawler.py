import os.path
import re

import nltk
import requests
from bs4 import BeautifulSoup
import time
import random
from collections import defaultdict
import csv
from nltk.corpus import stopwords

URL = "https://www.azlyrics.com/t/taylorswift.html"
PARENT_URL = "https://www.azlyrics.com"
PARENT_DIR = "word_frequencies/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36,gzip(gfe)"}
PROXIES = [
    'http://114.121.248.251:8080',
    'http://222.85.190.32:8090',
    'http://47.107.128.69:888',
    'http://41.65.146.38:8080',
    'http://190.63.184.11:8080',
    'http://45.7.135.34:999',
    'http://141.94.104.25:8080',
    'http://222.74.202.229:8080',
    'http://141.94.106.43:8080',
    'http://191.101.39.96:80'
]


# todo: make it a parallel crawler. i can parallely fetch all song lyrics.
# but do this only after metrics are converted into charts well
# since this does not change the data to be fetched.


class LyricsCrawler:

    def __init__(self, url):
        self.url = url
        self.proxy_index = 0

    def get_all_song_lyrics_urls(self, all_songs_page_url):
        r = requests.get(all_songs_page_url, headers=HEADERS)
        soup = BeautifulSoup(r.content, 'html5lib')
        song_urls = soup.findAll('div', {'class': 'listalbum-item'})
        return [self.canonicalize_url(song_url.a['href']) for song_url in song_urls]

    def canonicalize_url(self, relative_path):
        if relative_path.startswith(PARENT_URL):
            return relative_path
        else:
            return PARENT_URL + relative_path

    def get_word_list_for_song(self, url, stop_words):
        proxy = PROXIES[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(PROXIES)
        r = requests.get(url=url, headers=HEADERS,
                         proxies={'http': proxy, 'https': proxy})
        time.sleep(random.randint(5, 10))
        soup = BeautifulSoup(r.content, 'html.parser')
        # Find section which has song lyrics.
        lyrics = soup.find_all(lambda tag: tag.name == 'div' and not tag.attrs)[0].text
        symbols = "!@#$%^&*()_-+={[}]|\;:\"<>?/., "
        non_sanitized_words = lyrics.lower().split()
        sanitized_words = []
        for word in non_sanitized_words:
            for i in range(len(symbols)):
                word = word.replace(symbols[i], '')
            if word not in stop_words:
                sanitized_words.append(word)
        return sanitized_words

    def generate_dict(self, word_list):
        word_freq = {}
        word_freq = defaultdict(lambda: 0, word_freq)

        for word in word_list:
            # print ('word=', word)
            word_freq[word] += 1
        return word_freq

    def export_per_song_word_freq(self, url, word_list):
        song_name = self.get_song_name(url)
        print(f"Exporting metrics of song: {song_name}")
        word_freq = self.generate_dict(word_list)

        file_name = PARENT_DIR + song_name + ".csv"
        self.export_dict_to_csv(file_name, word_freq)

    def get_song_name(self, url):
        url = url.removesuffix(".html")
        prefix_regex = "https://.*/"
        return re.sub(f"^({prefix_regex})", "", url)

    def export_all_songs_word_freq(self, all_song_words_list):
        word_freq = self.generate_dict(all_song_words_list)
        file_name = PARENT_DIR + "all_song_freq.csv"
        self.export_dict_to_csv(file_name, word_freq)

    def export_dict_to_csv(self, file_name, word_freq):
        # Populate the file.
        with open(file_name, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in word_freq.items():
                writer.writerow([key, value])
        csv_file.close()

        # Make the file read-only.
        os.chmod(file_name, 0o444)

    def get_possibly_recorded_song_word_list(self, url):
        song_file = PARENT_DIR + self.get_song_name(url) + ".csv"

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
        print(song_lyrics_page_urls)

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
    crawler = LyricsCrawler(URL)
    crawler.crawl()
