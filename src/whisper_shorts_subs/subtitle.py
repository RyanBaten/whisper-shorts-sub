import cv2
import numpy as np
import tqdm


def create_segments(words, word_overlap_delay=0.5, max_segment_words=None):
    """Splits words into logical segments to display on the screen at a time.

    Args:
        words (List[faster_whisper.transcribe.Word]): The word list to break into segments.
        word_overlap_delay (float): The maximum time between words before a new segment is determined.
        max_segment_words (int): The maximum number of words in each segment.

    Returns:
        (List[List[faster_whisper.transcribe.Word]]): A list of segments of words formed by splitting the input.
    """
    max_segment_words = (
        max_segment_words if max_segment_words is not None else len(words) + 1
    )
    res = []
    current = [words[0]]
    for word in words[1:]:
        if (
            len(current) >= max_segment_words
            or current[-1].end + word_overlap_delay <= word.start
        ):
            res.append(current)
            current = [word]
        else:
            current.append(word)
    if len(current) > 0:
        res.append(current)
    return res


def add_text_with_outlines(
    image,
    text,
    orient=None,
    font=cv2.FONT_HERSHEY_TRIPLEX,
    font_scale=2,
    font_color=None,
    thickness=2,
    line_type=cv2.LINE_AA,
    outlines=None,
    inplace=True,
    orient_x_percent=0.5,
    orient_y_percent=0.5,
):
    """Add text with colored outlines to an image.

    Args:
        image (numpy.ndarray): The numpy array containing image data.
        text (string): The text to add to the image.
        orient (None or Tuple[int, int]): The Location of the text relative to the top left corner.
        font (int): The cv2 font to use.
        font_scale (float): The size of the text.
        font_color (Tuple[int, int, int]): Tuple containing ints 0-255 indicating bgr color.
        thickness (float): The thickness of the text.
        line_type (int): The cv2 line type.
        outlines (List[Dict]): Definitions of outline color and thicknesses. ex: [{'color': (0, 0, 0), 'thickness': 8}]
        inplace (bool): If True, will modify the image inplace.
        orient_x_percent (float): If orient is None, the percentage of the screen from the left at which the text should
            be centered horizontally.
        orient_y_percent (float): If orient is None, the percentage of the screen from the top at which the text should
            be centered vertically.

    Returns:
        (numpy.ndarray): The image data with text applied to it.
    """
    result = image
    if not inplace:
        result = np.copy(image)
    if orient is None:
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        orient = (
            int((image.shape[1] - text_size[0]) * orient_x_percent),
            int((image.shape[0] + text_size[1]) * orient_y_percent),
        )
    font_color = font_color if font_color is not None else (255, 255, 255)
    outlines = (
        outlines if outlines is not None else [{"color": (0, 0, 0), "thickness": 8}]
    )
    if isinstance(outlines, list):
        for outline in outlines:
            if (
                not isinstance(outline, dict)
                or "color" not in outline
                or "thickness" not in outline
            ):
                raise ValueError(
                    "Please provide outline options in the following format: [{'color': ..., 'thickness': ...}]"
                )
            cv2.putText(
                result,
                text,
                orient,
                font,
                font_scale,
                outline["color"],
                outline["thickness"],
                line_type,
            )
    result = cv2.putText(
        result, text, orient, font, font_scale, font_color, thickness, line_type
    )
    return result


def add_words_with_outlines(
    image,
    words,
    highlight_index=None,
    current_word_scale=1,
    orient=None,
    font=cv2.FONT_HERSHEY_TRIPLEX,
    font_scale=2,
    font_color=None,
    highlight_color=None,
    thickness=2,
    line_type=cv2.LINE_AA,
    outlines=None,
    inplace=True,
    orient_x_percent=0.5,
    orient_y_percent=0.5,
):
    """Add text with colored outlines to an image.

    Args:
        image (numpy.ndarray): The numpy array containing image data.
        words (List[string]): The words to add to the image.
        highlight_index (int): If provided, will highlight the nth word where n is highlight_index.
        current_word_scale (float): If provided, will multiply the scale of the word at highlight_index by this value.
        orient (None or Tuple[int, int]): The Location of the text relative to the top left corner.
        font (int): The cv2 font to use.
        font_scale (float): The size of the text.
        font_color (Tuple[int, int, int]): Tuple containing ints 0-255 indicating bgr color.
        highlight_color (Tuple[int, int, int]): If a word is highlighted, it will be displayed in this color.
        thickness (float): The thickness of the text.
        line_type (int): The cv2 line type.
        outlines (List[Dict]): Definitions of outline color and thicknesses. ex: [{'color': (0, 0, 0), 'thickness': 8}]
        inplace (bool): If True, will modify the image inplace.
        orient_x_percent (float): If orient is None, the percentage of the screen from the left at which the text should
            be centered horizontally.
        orient_y_percent (float): If orient is None, the percentage of the screen from the top at which the text should
            be centered vertically.

    Returns:
        (numpy.ndarray): The image data with text applied to it.
    """
    result = image
    if not inplace:
        result = np.copy(image)
    if orient is None:
        text_size = cv2.getTextSize(" ".join(words), font, font_scale, thickness)[0]
        orient = (
            int((image.shape[1] - text_size[0]) * orient_x_percent),
            int((image.shape[0] + text_size[1]) * orient_y_percent),
        )
    word_widths = [
        cv2.getTextSize(word, font, font_scale, thickness)[0][0] for word in words
    ]
    space_size = 0
    if len(word_widths) > 1:
        space_size = (text_size[0] - sum(word_widths)) / (len(word_widths) - 1)
    font_color = font_color if font_color is not None else (255, 255, 255)
    highlight_color = highlight_color if highlight_color is not None else (0, 0, 255)
    outlines = (
        outlines if outlines is not None else [{"color": (0, 0, 0), "thickness": 8}]
    )
    if isinstance(outlines, list):
        for outline in outlines:
            if (
                not isinstance(outline, dict)
                or "color" not in outline
                or "thickness" not in outline
            ):
                raise ValueError(
                    "Please provide outline options in the following format: [{'color': ..., 'thickness': ...}]"
                )
            current_x_offset = 0
            for ix, word in enumerate(words):
                scale = (
                    current_word_scale * font_scale
                    if ix == highlight_index
                    else font_scale
                )
                word_width = cv2.getTextSize(word, font, scale, thickness)[0][0]
                cv2.putText(
                    result,
                    word,
                    (int(orient[0] + current_x_offset), orient[1]),
                    font,
                    scale,
                    outline["color"],
                    outline["thickness"],
                    line_type,
                )
                current_x_offset += word_width + space_size
    current_x_offset = 0
    for ix, word in enumerate(words):
        color = highlight_color if ix == highlight_index else font_color
        scale = current_word_scale * font_scale if ix == highlight_index else font_scale
        word_width = cv2.getTextSize(word, font, scale, thickness)[0][0]
        cv2.putText(
            result,
            word,
            (int(orient[0] + current_x_offset), orient[1]),
            font,
            scale,
            color,
            thickness,
            line_type,
        )
        current_x_offset += word_width + space_size
    return result


def create_subtitled_video(
    video,
    outfile,
    segments,
    orient=None,
    font=cv2.FONT_HERSHEY_TRIPLEX,
    font_scale=2,
    font_color=None,
    thickness=2,
    line_type=cv2.LINE_AA,
    outlines=None,
    inplace=True,
    orient_x_percent=0.5,
    orient_y_percent=0.5,
    current_word_scale=1,
    strategy="whole_segment",
):
    """Processes an entire input video, creating an output video with subtitles but no audio.

    Args:

    Returns:
    """
    cap = cv2.VideoCapture(video)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(outfile, fourcc, fps, (frame_width, frame_height))
    segment_index = 0
    for _ in tqdm.tqdm(range(length)):
        ret, frame = cap.read()
        if not ret:
            break
        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if segment_index >= len(segments):
            out.write(frame)
            continue
        if timestamp > segments[segment_index][-1].end:
            segment_index += 1
            if segment_index >= len(segments):
                out.write(frame)
                continue
        if timestamp < segments[segment_index][0].start:
            out.write(frame)
            continue
        if strategy == "highlight":
            words = []
            highlight_index = None
            for ix, word in enumerate(segments[segment_index]):
                words.append(word.word.strip())
                if (timestamp > word.start) and (timestamp <= word.end):
                    highlight_index = ix
            frame = add_words_with_outlines(
                frame,
                words,
                highlight_index=highlight_index,
                current_word_scale=current_word_scale,
                orient=orient,
                font=font,
                font_scale=font_scale,
                font_color=font_color,
                thickness=thickness,
                line_type=line_type,
                outlines=outlines,
                inplace=inplace,
                orient_x_percent=orient_x_percent,
                orient_y_percent=orient_y_percent,
            )
            out.write(frame)
            continue
        if strategy == "type":
            current_text = " ".join(
                [
                    word.word.strip()
                    for word in segments[segment_index]
                    if timestamp > word.start
                ]
            )
        else:
            current_text = " ".join(
                [word.word.strip() for word in segments[segment_index]]
            )
        frame = add_text_with_outlines(
            frame,
            current_text,
            orient=orient,
            font=font,
            font_scale=font_scale,
            font_color=font_color,
            thickness=thickness,
            line_type=line_type,
            outlines=outlines,
            inplace=inplace,
            orient_x_percent=orient_x_percent,
            orient_y_percent=orient_y_percent,
        )
        out.write(frame)
    cap.release()
    out.release()
