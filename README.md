# taylorSwiftUniqueWords
Crawler to get frequency of unique words used by an artist (started with Taylor Swift, hence the name:) across all their songs, as well as per song.

# Usage
Just pass `--artist` argument and run it using python.

# Output
* Exports `.csv` files per song
* As well as an `all_song_freq.csv` file, each of which contain a sorted order of unique words used, in descending order of their frequency.
* Generates a graph of top 50 words used by the artist, across all songs.

It makes sure that pronouns, articles and prepositions are not counted, to avoid noise in the list!
