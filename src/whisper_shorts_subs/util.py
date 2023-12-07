from faster_whisper.transcribe import Word


def words_to_string(words, delim="\t"):
    """Converts transcription data to formatted string.

    Args:
        words (List[faster_whisper.transcribe.Word]): List of data containing transcribed words.
        delim (str): The delimiter to place between columns of transcription data.

    Returns:
        (str): Formatted string containing transcription word data.
    """
    res = f"WORD{delim}START{delim}END{delim}PROBABILITY\n"
    for word in words:
        res += f"{word.word}{delim}{word.start:.2f}{delim}{word.end:.2f}{delim}{word.probability:.3f}\n"
    return res.strip("\n")


def string_to_words(word_string, delim="\t"):
    """Parses formatted string into faster_whisper words.

    Args:
        word_string (str): Formatted string as output by words_to_string. Data split by delimiter.
        delim (str): The delimiter between columns in the word_string.

    Returns:
        (List[faster_whisper.transcribe.Word]): List of word data parsed from the input string.
    """
    res = []
    for line in word_string.split("\n")[1:]:
        word, start, end, prob = line.split(delim)
        res.append(Word(float(start), float(end), word, float(prob)))
    return res
