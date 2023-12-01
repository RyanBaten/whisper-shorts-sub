import moviepy.editor as mp


def add_movie_audio(audio_source, video_source, outfile):
    """Copies audio from an audio source, video from a video source, and creates a final video."""
    audio = mp.VideoFileClip(audio_source).audio
    video = mp.VideoFileClip(video_source)
    final = video.set_audio(audio)
    final.write_videofile(outfile)
