from faster_whisper.transcribe import Word
from whisper_shorts_subs.util import words_to_string, string_to_words


def test_words_to_string():
    words = [
        Word(0.1, 1.1, "apple", 0.8),
        Word(1.4, 2.1, "orange", 0.9),
        Word(3.1, 4.6, "grapefruit", 0.745),
        Word(5.2, 6.09, "pear", 0.82),
    ]
    assert (
        words_to_string(words)
        == "WORD\tSTART\tEND\tPROBABILITY\napple\t0.10\t1.10\t0.800\norange\t1.40\t2.10\t0.900\ngrapefruit\t3.10\t4.60\t0.745\npear\t5.20\t6.09\t0.820"
    )


def test_string_to_words():
    string_to_parse = "WORD\tSTART\tEND\tPROBABILITY\napple\t0.10\t1.10\t0.800\norange\t1.40\t2.10\t0.900\ngrapefruit\t3.10\t4.60\t0.745\npear\t5.20\t6.09\t0.820"
    words = [
        Word(0.1, 1.1, "apple", 0.8),
        Word(1.4, 2.1, "orange", 0.9),
        Word(3.1, 4.6, "grapefruit", 0.745),
        Word(5.2, 6.09, "pear", 0.82),
    ]
    word_output = string_to_words(string_to_parse)
    assert len(words) == len(word_output)
    for ref_word, parsed_word in zip(words, word_output):
        assert (
            (ref_word.word == parsed_word.word)
            and (ref_word.start == parsed_word.start)
            and (ref_word.end == parsed_word.end)
            and (ref_word.probability == parsed_word.probability)
        )
