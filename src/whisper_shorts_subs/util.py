from faster_whisper.transcribe import Word


def words_to_string(words, delim='\t'):
    res = "WORD\tSTART\tEND\tPROBABILITY\n"
    for word in words:
        res += f"{word.word}{delim}{word.start:.2f}{delim}{word.end:.2f}{delim}{word.probability:.3f}\n"
    return res.strip('\n')


def string_to_words(word_string, delim='\t'):
    res = []
    for line in word_string.split('\n')[1:]:
        word, start, end, prob = line.split(delim)
        res.append(Word(float(start), float(end), word, float(prob)))
    return res
