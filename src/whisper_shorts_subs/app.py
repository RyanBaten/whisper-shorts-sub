import customtkinter
from tkinter import CENTER, filedialog, Canvas, PhotoImage
from faster_whisper import WhisperModel

import threading
import queue
import tempfile
import numpy as np
import cv2
import os

from PIL import Image, ImageTk

from .audio import add_movie_audio
from .subtitle import create_segments, create_subtitled_video, add_text_with_outlines, add_words_with_outlines
from .transcribe import transcribe_with_timestamps
from .util import string_to_words, words_to_string

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")


class App(customtkinter.CTk):
    """The UI for the whisper_shorts_subs tool."""

    def __init__(
        self,
        model_size="small",
        model_kwargs=None,
        canvas_width=180,
        canvas_height=320,
        words_per_segment=5,
        font_scale=2,
        outline_scale=8,
        orient_y_percent=0.5
    ):
        super().__init__()
        self.model_kwargs = model_kwargs if model_kwargs is not None else {"device": "cpu", "compute_type": "int8"}
        self.model = WhisperModel(model_size, **self.model_kwargs)
        self.transcription_queue = queue.Queue()
        self.export_queue = queue.Queue()
        self.input_video = ""
        self.font_scale = font_scale
        self.orient_y_percent = orient_y_percent
        self.words_per_segment = words_per_segment
        self.outline_scale = outline_scale
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.canvas_image = None

        self.title("whisper-shorts-subs")
        self.geometry(f"{1024}x{512}")

        self.grid_rowconfigure(14, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.textbox = customtkinter.CTkTextbox(self)
        self.textbox.grid(column=0, row=0, rowspan=15, sticky="nsew", padx=5, pady=5)

        self.button_load_video = customtkinter.CTkButton(self, text="Transcribe Video", command=self.transcribe_video)
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
            command=lambda x: self.set_and_update_canvas("orient_y_percent", x)
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
            command=lambda x: self.set_and_update_canvas("font_scale", x)
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
            command=lambda x: self.set_and_update_canvas("words_per_segment", x)
        )
        self.segment_words_slider.set(self.words_per_segment)
        self.segment_words_slider.grid(column=2, row=3)

        self.outline_scale_slider_label = customtkinter.CTkLabel(self, text="outline scale:")
        self.outline_scale_slider_label.grid(column=1, row=4)
        self.outline_scale_slider = customtkinter.CTkSlider(
            self,
            from_=6,
            to=30,
            number_of_steps=24,
            width=width,
            command=lambda x: self.set_and_update_canvas("outline_scale", x)
        )
        self.outline_scale_slider.set(self.outline_scale)
        self.outline_scale_slider.grid(column=2, row=4)

        self.highlight_checkbox_label = customtkinter.CTkLabel(self, text="color current word:")
        self.highlight_checkbox_label.grid(column=1, row=5)
        self.strategy = customtkinter.StringVar(value="highlight")
        self.highlight_checkbox = customtkinter.CTkCheckBox(self, text="", command=self.update_canvas,
                                                            variable=self.strategy, onvalue="highlight", offvalue="off")
        self.highlight_checkbox.select()
        self.highlight_checkbox.grid(column=2, row=5, sticky="w", padx=5)

        self.button_export_video = customtkinter.CTkButton(self, text="Export Video", command=self.export_video)
        self.button_export_video.grid(column=1, row=6, padx=5, pady=24, columnspan=2)

        self.status_label = customtkinter.CTkLabel(self, text="status", fg_color="transparent", wraplength=width, justify=CENTER)
        self.status_label.grid(column=1, row=7, columnspan=2, sticky="n")
        self.status_label.grid_remove()
        self.progress_bar = customtkinter.CTkProgressBar(self, orientation="horizontal", width=width)
        self.progress_bar.configure(mode="indeterminate", indeterminate_speed=1)
        self.progress_bar.grid(column=1, row=8, columnspan=2, sticky="n", padx=5, pady=5)
        self.progress_bar.grid_remove()

        self.preview_canvas = Canvas(self, width=self.canvas_width, height=self.canvas_height)
        self.preview_canvas.grid(column=4, row=0, rowspan=15, sticky="n", padx=5, pady=5)
        self.update_canvas()

    def update_canvas(self):
        width, height = 1080, 1920
        image = np.zeros((height, width, 3), np.uint8)
        image[:,:,1] = 180
        words = ["text" for _ in range(int(self.words_per_segment))]
        if self.strategy.get() == "highlight":
            image = add_words_with_outlines(
                image,
                words,
                highlight_index=0,
                font_scale=self.font_scale,
                orient_y_percent=self.orient_y_percent,
                outlines=[{'color': (0, 0, 0), 'thickness': int(self.outline_scale)}]
            )
        else:
            text = " ".join(words)
            image = add_text_with_outlines(
                image,
                text,
                font_scale=self.font_scale,
                orient_y_percent=self.orient_y_percent,
                outlines=[{'color': (0, 0, 0), 'thickness': int(self.outline_scale)}]
            )
        image = cv2.resize(image, (self.canvas_width, self.canvas_height), interpolation=cv2.INTER_AREA)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.canvas_image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.preview_canvas.create_image(0, 0, anchor="nw", image=self.canvas_image)

    def set_and_update_canvas(self, attribute_name, value):
        setattr(self, attribute_name, value)
        self.update_canvas()

    def disable_buttons(self):
        self.button_load_video.configure(state="disabled")
        self.button_export_video.configure(state="disabled")

    def enable_buttons(self):
        self.button_load_video.configure(state="normal")
        self.button_export_video.configure(state="normal")

    def transcribe_video(self):
        filename = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("mp4 files", "*.mp4")]
        )
        if len(filename) == 0:
            return
        print(filename)
        self.input_video = filename
        self.disable_buttons()
        self.status_label.configure(text="transcribing...")
        self.status_label.grid()
        self.progress_bar.grid()
        self.progress_bar.start()
        TranscriptionWorker(self.transcription_queue, self.model, self.input_video).start()
        self.after(500, self.poll_transcribe_results)

    def poll_transcribe_results(self):
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
        if self.input_video == "":
            self.status_label.configure(text="Please transcribe a video before exporting.")
            self.status_label.grid()
            return
        filename = filedialog.asksaveasfilename(
            title="Select an output filename",
            filetypes=[("mp4 files", "*.mp4")]
        )
        if filename == '':
            return
        try:
            words = string_to_words(self.textbox.get("0.0", "end").strip('\n'))
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
            outlines=[{'color': (0, 0, 0), 'thickness': int(self.outline_scale)}],
            strategy=self.strategy.get()
        ).start()
        self.after(500, self.poll_export_results())

    def poll_export_results(self):
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
    def __init__(self, transcribe_queue, model, filename):
        self.queue = transcribe_queue
        self.model = model
        self.filename = filename
        super().__init__()

    def run(self):
        words = transcribe_with_timestamps(self.model, self.filename)
        self.queue.put(words)


class ExportWorker(threading.Thread):
    def __init__(self, export_queue, filename, input_video, segments, **subtitle_kwargs):
        self.queue = export_queue
        self.filename = filename
        self.input_video = input_video
        self.segments = segments
        self.subtitle_kwargs = subtitle_kwargs
        super().__init__()

    def run(self):
        processed_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        processed_video.close()
        create_subtitled_video(
            self.input_video,
            processed_video.name,
            self.segments,
            **self.subtitle_kwargs
        )
        self.queue.put("audio")
        add_movie_audio(self.input_video, processed_video.name, self.filename)
        os.remove(processed_video.name)
        self.queue.put("done")


def run_app():
    """Entrypoint for executable."""
    app = App()
    app.mainloop()
