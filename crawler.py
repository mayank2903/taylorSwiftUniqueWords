import os.path
import re
import requests
from bs4 import BeautifulSoup
import time
import random
from collections import defaultdict
import csv

URL = "https://www.azlyrics.com/t/taylorswift.html"
PARENT_URL = "https://www.azlyrics.com"
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"}


def get_all_song_urls(all_songs_page_url):
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


def get_word_list_for_song(url):
    r = requests.get(url=url, headers=HEADERS)
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
    print("exporting metrics of song: ", song_name)
    word_freq = generate_dict(word_list)

    file_name = song_name + ".csv"
    export_dict_to_csv(file_name, word_freq)


def get_song_name(url):
    url = url.removesuffix(".html")
    prefix_regex = "https://.*/"
    return re.sub(f"^({prefix_regex})", "", url)


def export_all_songs_word_freq(all_song_words_list):
    word_freq = generate_dict(all_song_words_list)
    file_name = "all_song_freq.csv"
    export_dict_to_csv(file_name, word_freq)


# todo: make this export readonly csv ?
def export_dict_to_csv(file_name, word_freq):
    with open(file_name, 'w') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in word_freq.items():
            writer.writerow([key, value])


def main():
    all_song_urls = get_all_song_urls(URL)
    number_of_songs = len(all_song_urls)
    print(f"{number_of_songs} songs found")

    # Sorting links by the song names. Helps track how far we are in crawling.
    all_song_urls = sorted(all_song_urls, reverse=True)
    print(all_song_urls)

    # Collect all words of all songs by the artist.
    all_song_words = []
    i = 0
    for url in all_song_urls:
        i += 1
        print(f"[{i}/{number_of_songs}] Getting lyrics for: ", url)

        # check if metrics for this song already exported.
        # todo: extract this into its own method.
        song_file = get_song_name(url) + ".csv"
        try:
            if os.path.exists(song_file):
                print(f"{song_file} already exported. Skipping..")
                continue
        except FileNotFoundError:
            pass

        word_list = get_word_list_for_song(url)
        all_song_words = all_song_words + word_list
        # export per-song stats
        export_per_song_word_freq(url, word_list)

    # export all songs' collective stats
    export_all_songs_word_freq(all_song_words)
    return all_song_words


if __name__ == "__main__":
    main()
