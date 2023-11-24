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


# todo: make it a parallel crawler. i can parallely fetch all song lyrics.
# but do this only after metrics are converted into charts well
# since this does not change the data to be fetched.

def get_all_song_lyrics_urls(all_songs_page_url):
    r = requests.get(all_songs_page_url, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html5lib')
    time.sleep(10)
    song_urls = soup.findAll('div', {'class': 'listalbum-item'})
    return [canonicalize_url(song_url.a['href']) for song_url in song_urls]


def canonicalize_url(relative_path):
    if relative_path.startswith(PARENT_URL):
        return relative_path
    else:
        return PARENT_URL + relative_path


def get_word_list_for_song(url, stop_words):
    r = requests.get(url=url, headers=HEADERS)
    time.sleep(random.randint(30, 40))
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


def generate_dict(word_list):
    word_freq = {}
    word_freq = defaultdict(lambda: 0, word_freq)

    for word in word_list:
        # print ('word=', word)
        word_freq[word] += 1
    return word_freq


def export_per_song_word_freq(url, word_list):
    song_name = get_song_name(url)
    print(f"Exporting metrics of song: {song_name}")
    word_freq = generate_dict(word_list)

    file_name = PARENT_DIR + song_name + ".csv"
    export_dict_to_csv(file_name, word_freq)


def get_song_name(url):
    url = url.removesuffix(".html")
    prefix_regex = "https://.*/"
    return re.sub(f"^({prefix_regex})", "", url)


def export_all_songs_word_freq(all_song_words_list):
    word_freq = generate_dict(all_song_words_list)
    file_name = PARENT_DIR + "all_song_freq.csv"
    export_dict_to_csv(file_name, word_freq)


def export_dict_to_csv(file_name, word_freq):
    # Populate the file.
    with open(file_name, 'w') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in word_freq.items():
            writer.writerow([key, value])
    csv_file.close()

    # Make the file read-only.
    os.chmod(file_name, 0o444)


def get_possibly_recorded_song_word_list(url):
    song_file = PARENT_DIR + get_song_name(url) + ".csv"

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


def main():
    song_lyrics_page_urls = get_all_song_lyrics_urls(URL)
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
        word_list = get_possibly_recorded_song_word_list(song_lyrics_page_url)

        # If nothing recorded yet, crawl through lyrics page.
        if len(word_list) == 0:
            # Get and export per-song stats
            word_list = get_word_list_for_song(song_lyrics_page_url, stop_words)
            export_per_song_word_freq(song_lyrics_page_url, word_list)

        # Add result to all song words list.
        all_song_words = all_song_words + word_list

    # Export all songs' collective stats, provided we managed to crawl over all songs.
    if i == number_of_songs != 0:
        print('Exporting all song frequencies...')
        export_all_songs_word_freq(all_song_words)


if __name__ == "__main__":
    main()
