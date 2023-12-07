import moviepy.editor as mp


def add_movie_audio(audio_source, video_source, outfile, codec="libx264"):
    """Copies audio from an audio source, video from a video source, and creates a final video.

    Args:
        audio_source (str): The filepath to the file containing the audio source.
        video_source (str): The filepath to the file containing the video source.
        outfile (str): The filepath to create the composited video at.
        codec (str): The codec to use to write the file.
    """
    audio = mp.VideoFileClip(audio_source).audio
    video = mp.VideoFileClip(video_source)
    final = video.set_audio(audio)
    final.write_videofile(outfile, codec=codec)
