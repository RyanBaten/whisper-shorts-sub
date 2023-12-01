from faster_whisper.transcribe import Word
import re


def transcribe_with_timestamps(model, audio, lowercase=False, uppercase=False, remove_punctuation=False):
    """Transcribes a file's audio into Word objects containing the words and their start and end times.

    Args:
        model (faster_whisper.WhisperModel): The loaded whisper model to use for transcription.
        audio (Union[str, BinaryIO, numpy.ndarray]): An input audio filename or content for model.transcribe.
        lowercase (bool): If True, will ensure all words in the output are lowercase.
        uppercase (bool): If True, will ensure all words in the output are uppercase. Has precedence over lowercase.
        remove_punctuation (bool): If True, will ensure all words in the output contain no punctuation.

    Returns:
        (List[faster_whisper.transcribe.Word]): Sequence of words inferred from the audio file.
    """
    segments, _ = model.transcribe(audio, word_timestamps=True)
    res = []
    for segment in segments:
        for word in segment.words:
            text = word.word
            if lowercase:
                text = text.lower()
            if uppercase:
                text = text.upper()
            if remove_punctuation:
                text = re.sub(r'[^\w\s]', '', text)
            res.append(Word(word.start, word.end, text, word.probability))
    return res
