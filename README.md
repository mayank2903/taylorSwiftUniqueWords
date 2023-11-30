# taylorSwiftUniqueWords
Crawler to get frequency of unique words used by an artist (started with Taylor Swift, hence the name:) across all their songs, as well as per song.

# Usage
Check commented note in `crawler.py` file. Just change the `URL` and `PARENT_DIR` variables to the artist that you want. 
Format for `URL`: Just put (first letter of artist name)/(artistNameWithoutSpace)
Format for `PARENT_DIR`: You can just put artistNameWithoutSpace again, or whatever you like.

# Output
It exports csv files per song, as well as an `all_song_freq.csv` file, each of which contain a sorted order of unique words used, in descending order of their frequency.
