import customtkinter
from tkinter import CENTER, filedialog, Canvas
from faster_whisper import WhisperModel

import threading
import queue
import tempfile
import numpy as np
import cv2
import os
import platform

from PIL import Image, ImageTk

from .audio import add_movie_audio
from .subtitle import (
    create_segments,
    create_subtitled_video,
    add_text_with_outlines,
    add_words_with_outlines,
)
from .transcribe import transcribe_with_timestamps
from .util import string_to_words, words_to_string

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")


class App(customtkinter.CTk):
    """The UI for the whisper_shorts_subs tool.

    Args:
        model_size (str): String descriptor for the model to use.
        model_kwargs (dict): Keyword arguments to model loading.
        canvas_width (int): Preview canvas width in pixels.
        canvas_height (int): Preview canvas height in pixels.
        words_per_segment (int): Default number of max words to show.
        font_scale (float): Default text size.
        outline_scale (float): Default outline size.
        orient_y_percent (float): Default Y position of text.
        current_word_scale (float): Multiplier on current highlighted word size.
    """

    def __init__(
        self,
        model_size="small",
        model_kwargs=None,
        canvas_width=180,
        canvas_height=320,
        words_per_segment=5,
        font_scale=2,
        outline_scale=8,
        orient_y_percent=0.5,
        current_word_scale=1,
    ):
        super().__init__()
        self.model_kwargs = (
            model_kwargs
            if model_kwargs is not None
            else {"device": "cpu", "compute_type": "int8"}
        )
        self.model = WhisperModel(model_size, **self.model_kwargs)
        self.transcription_queue = queue.Queue()
        self.export_queue = queue.Queue()
        self.input_video = ""
        self.font_scale = font_scale
        self.orient_y_percent = orient_y_percent
        self.words_per_segment = words_per_segment
        self.outline_scale = outline_scale
        self.current_word_scale = current_word_scale
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.canvas_image = None

        self.title("whisper-shorts-subs")
        self.geometry(f"{1024}x{512}")

        self.grid_rowconfigure(14, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.textbox = customtkinter.CTkTextbox(self)
        self.textbox.grid(column=0, row=0, rowspan=15, sticky="nsew", padx=5, pady=5)

        self.button_load_video = customtkinter.CTkButton(
            self, text="Transcribe Video", command=self.transcribe_video
        )
        self.button_load_video.grid(column=1, row=0, padx=5, pady=24, columnspan=2)
        width = self.button_load_video.winfo_reqwidth()

        self.y_slider_label = customtkinter.CTkLabel(self, text="Y:")
        self.y_slider_label.grid(column=1, row=1)
        self.y_slider = customtkinter.CTkSlider(
            self,
            from_=0,
            to=0.8,
            number_of_steps=16,
            width=width,
            command=lambda x: self.set_and_update_canvas("orient_y_percent", x),
        )
        self.y_slider.set(0.5)
        self.y_slider.grid(column=2, row=1)

        self.font_scale_slider_label = customtkinter.CTkLabel(self, text="font scale:")
        self.font_scale_slider_label.grid(column=1, row=2)
        self.font_scale_slider = customtkinter.CTkSlider(
            self,
            from_=0.1,
            to=4,
            number_of_steps=20,
            width=width,
            command=lambda x: self.set_and_update_canvas("font_scale", x),
        )
        self.font_scale_slider.set(self.font_scale)
        self.font_scale_slider.grid(column=2, row=2)

        self.segment_words_slider_label = customtkinter.CTkLabel(self, text="# words:")
        self.segment_words_slider_label.grid(column=1, row=3)
        self.segment_words_slider = customtkinter.CTkSlider(
            self,
            from_=1,
            to=8,
            number_of_steps=8,
            width=width,
            command=lambda x: self.set_and_update_canvas("words_per_segment", x),
        )
        self.segment_words_slider.set(self.words_per_segment)
        self.segment_words_slider.grid(column=2, row=3)

        self.outline_scale_slider_label = customtkinter.CTkLabel(
            self, text="outline scale:"
        )
        self.outline_scale_slider_label.grid(column=1, row=4)
        self.outline_scale_slider = customtkinter.CTkSlider(
            self,
            from_=6,
            to=30,
            number_of_steps=24,
            width=width,
            command=lambda x: self.set_and_update_canvas("outline_scale", x),
        )
        self.outline_scale_slider.set(self.outline_scale)
        self.outline_scale_slider.grid(column=2, row=4)

        self.highlight_checkbox_label = customtkinter.CTkLabel(
            self, text="color current word:"
        )
        self.highlight_checkbox_label.grid(column=1, row=5)
        self.strategy = customtkinter.StringVar(value="highlight")
        self.highlight_checkbox = customtkinter.CTkCheckBox(
            self,
            text="",
            command=self.update_canvas,
            variable=self.strategy,
            onvalue="highlight",
            offvalue="off",
        )
        self.highlight_checkbox.select()
        self.highlight_checkbox.grid(column=2, row=5, sticky="w", padx=5)
        self.current_word_scale_slider_label = customtkinter.CTkLabel(
            self, text="current word scale:"
        )
        self.current_word_scale_slider_label.grid(column=1, row=6)
        self.current_word_scale_slider = customtkinter.CTkSlider(
            self,
            from_=0.5,
            to=2,
            number_of_steps=15,
            width=width,
            command=lambda x: self.set_and_update_canvas("current_word_scale", x),
        )
        self.current_word_scale_slider.set(self.current_word_scale)
        self.current_word_scale_slider.grid(column=2, row=6)

        self.button_export_video = customtkinter.CTkButton(
            self, text="Export Video", command=self.export_video
        )
        self.button_export_video.grid(column=1, row=7, padx=5, pady=24, columnspan=2)

        self.status_label = customtkinter.CTkLabel(
            self,
            text="status",
            fg_color="transparent",
            wraplength=width,
            justify=CENTER,
        )
        self.status_label.grid(column=1, row=8, columnspan=2, sticky="n")
        self.status_label.grid_remove()
        self.progress_bar = customtkinter.CTkProgressBar(
            self, orientation="horizontal", width=width
        )
        self.progress_bar.configure(mode="indeterminate", indeterminate_speed=1)
        self.progress_bar.grid(
            column=1, row=9, columnspan=2, sticky="n", padx=5, pady=5
        )
        self.progress_bar.grid_remove()

        self.preview_canvas = Canvas(
            self, width=self.canvas_width, height=self.canvas_height
        )
        self.preview_canvas.grid(
            column=4, row=0, rowspan=15, sticky="n", padx=5, pady=5
        )
        self.update_canvas()

    def update_canvas(self):
        """Updates the image displayed on the preview canvas."""
        width, height = 1080, 1920
        image = np.zeros((height, width, 3), np.uint8)
        image[:, :, 1] = 180
        words = ["text" for _ in range(int(self.words_per_segment))]
        if self.strategy.get() == "highlight":
            image = add_words_with_outlines(
                image,
                words,
                highlight_index=0,
                current_word_scale=self.current_word_scale,
                font_scale=self.font_scale,
                orient_y_percent=self.orient_y_percent,
                outlines=[{"color": (0, 0, 0), "thickness": int(self.outline_scale)}],
            )
        else:
            text = " ".join(words)
            image = add_text_with_outlines(
                image,
                text,
                font_scale=self.font_scale,
                orient_y_percent=self.orient_y_percent,
                outlines=[{"color": (0, 0, 0), "thickness": int(self.outline_scale)}],
            )
        image = cv2.resize(
            image, (self.canvas_width, self.canvas_height), interpolation=cv2.INTER_AREA
        )
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.canvas_image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.preview_canvas.create_image(0, 0, anchor="nw", image=self.canvas_image)

    def set_and_update_canvas(self, attribute_name, value):
        """Sets a class attribute and updates the preview canvas.

        Args:
            attribute_name (str): The attribute name to change.
            value: The attribute value.
        """
        setattr(self, attribute_name, value)
        self.update_canvas()

    def disable_buttons(self):
        """Disables UI buttons to prevent the user from spamming actions that spawn threads."""
        self.button_load_video.configure(state="disabled")
        self.button_export_video.configure(state="disabled")

    def enable_buttons(self):
        """Enables UI buttons."""
        self.button_load_video.configure(state="normal")
        self.button_export_video.configure(state="normal")

    def transcribe_video(self):
        """Spawns a worker to transcribe a video with an audio source."""
        filename = filedialog.askopenfilename(
            title="Select a File", filetypes=[("mp4 files", "*.mp4")]
        )
        if len(filename) == 0:
            return
        self.input_video = filename
        self.disable_buttons()
        self.status_label.configure(text="transcribing...")
        self.status_label.grid()
        self.progress_bar.grid()
        self.progress_bar.start()
        TranscriptionWorker(
            self.transcription_queue, self.model, self.input_video
        ).start()
        self.after(500, self.poll_transcribe_results)

    def poll_transcribe_results(self):
        """Waits on transcription results."""
        try:
            words = self.transcription_queue.get_nowait()
            self.textbox.delete("0.0", "end")
            self.textbox.insert("0.0", words_to_string(words))
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.status_label.grid_remove()
            self.enable_buttons()
        except queue.Empty:
            self.after(500, self.poll_transcribe_results)

    def export_video(self):
        """Spawns a worker to work on video export."""
        if self.input_video == "":
            self.status_label.configure(
                text="Please transcribe a video before exporting."
            )
            self.status_label.grid()
            return
        filename = filedialog.asksaveasfilename(
            title="Select an output filename", filetypes=[("mp4 files", "*.mp4")]
        )
        filename = os.path.splitext(filename)[0] + '.mp4'
        if filename == "":
            return
        try:
            words = string_to_words(self.textbox.get("0.0", "end").strip("\n"))
        except Exception:
            self.status_label.configure(text="Error in transcript format")
            self.status_label.grid()
            return
        self.disable_buttons()
        segments = create_segments(words, max_segment_words=int(self.words_per_segment))
        self.status_label.configure(text="Generating subtitled video...")
        self.status_label.grid()
        self.progress_bar.grid()
        self.progress_bar.start()
        ExportWorker(
            self.export_queue,
            filename,
            self.input_video,
            segments,
            font_scale=self.font_scale,
            orient_y_percent=self.orient_y_percent,
            outlines=[{"color": (0, 0, 0), "thickness": int(self.outline_scale)}],
            strategy=self.strategy.get(),
            current_word_scale=self.current_word_scale,
        ).start()
        self.after(500, self.poll_export_results())

    def poll_export_results(self):
        """Waits on export results."""
        try:
            status = self.export_queue.get_nowait()
            if status == "audio":
                self.status_label.configure(text="Adding audio from original...")
                self.after(500, self.poll_export_results)
                return
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.status_label.grid_remove()
            self.enable_buttons()
        except queue.Empty:
            self.after(500, self.poll_export_results)


class TranscriptionWorker(threading.Thread):
    """A thread worker to transcribe the audio within a mp4.

    Args:
        transcribe_queue (queue.Queue): The queue to post results to.
        model (faster_whisper.WhisperModel): The whisper model to use for transcription.
        filename (str): File path to mp4 file containing audio to transcribe.
    """

    def __init__(self, transcribe_queue, model, filename):
        self.queue = transcribe_queue
        self.model = model
        self.filename = filename
        super().__init__(daemon=True)

    def run(self):
        """Runs transcription."""
        words = transcribe_with_timestamps(self.model, self.filename)
        self.queue.put(words)


class ExportWorker(threading.Thread):
    """A thread worker to generate a final video with subtitles.

    Args:
        export_queue (queue.Queue): Queue used to communicate status to the UI.
        filename (str): File path to put the output mp4 at.
        input_video (str):  File path containing the original video with audio source.
        segments (List[List[faster_whisper.transcribe.Word]]): Segments containing the words to display on the screen at the same time.
        **subtitle_kwargs: Additional keyword arguments to be passed to whisper_shorts_subs.subtitle.create_subtitled_video.
    """

    def __init__(
        self, export_queue, filename, input_video, segments, **subtitle_kwargs
    ):
        self.queue = export_queue
        self.filename = filename
        self.input_video = input_video
        self.segments = segments
        self.subtitle_kwargs = subtitle_kwargs
        super().__init__(daemon=True)

    def run(self):
        """Creates video with subtitles."""
        processed_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        processed_video.close()
        create_subtitled_video(
            self.input_video,
            processed_video.name,
            self.segments,
            **self.subtitle_kwargs,
        )
        self.queue.put("audio")
        add_movie_audio(self.input_video, processed_video.name, os.path.normpath(self.filename))
        os.remove(processed_video.name)
        self.queue.put("done")


def run_app():
    """Entrypoint for executable."""
    app = App()
    app.mainloop()
