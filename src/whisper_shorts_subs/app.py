import customtkinter
from tkinter import CENTER, filedialog
from faster_whisper import WhisperModel

import threading
import queue
import tempfile
import os

from .audio import add_movie_audio
from .subtitle import create_segments, create_subtitled_video
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
        transcribe_kwargs=None,
        subtitle_kwargs=None
    ):
        super().__init__()
        self.model_kwargs = model_kwargs if model_kwargs is not None else {"device": "cpu", "compute_type": "int8"}
        self.transcribe_kwargs = transcribe_kwargs if transcribe_kwargs is not None else {}
        self.subtitle_kwargs = subtitle_kwargs if subtitle_kwargs is not None else {}
        self.model = WhisperModel(model_size, **self.model_kwargs)
        self.transcription_queue = queue.Queue()
        self.input_video = ""

        self.title("whisper-shorts-subs")
        self.geometry(f"{1000}x{300}")

        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.textbox = customtkinter.CTkTextbox(self)
        self.textbox.grid(column=0, row=0, rowspan=7, sticky="nsew", padx=5, pady=5)

        self.button_load_video = customtkinter.CTkButton(self, text="Transcribe Video", command=self.transcribe_video)
        self.button_load_video.grid(column=1, row=0, sticky="n", padx=5, pady=5)
        self.button_export_video = customtkinter.CTkButton(self, text="Export Video", command=self.export_video)
        self.button_export_video.grid(column=1, row=1, sticky="n", padx=5, pady=5)

        width = self.button_load_video.winfo_reqwidth()
        self.status_label = customtkinter.CTkLabel(self, text="status", fg_color="transparent", wraplength=width, justify=CENTER)
        self.status_label.grid(column=1, row=2, sticky="n")
        self.status_label.grid_remove()
        self.progress_bar = customtkinter.CTkProgressBar(self, orientation="horizontal", width=width)
        self.progress_bar.configure(mode="indeterminate", indeterminate_speed=1)
        self.progress_bar.grid(column=1, row=3, sticky="sew", padx=5, pady=5)
        self.progress_bar.grid_remove()

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
        TranscriptionWorker(self.transcription_queue, self.model, self.input_video, **self.transcribe_kwargs).start()
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
        except Exception:  # TODO: fix broad exception clause
            self.status_label.configure(text="Error in transcript format")
            self.status_label.grid()
            return
        self.disable_buttons()
        segments = create_segments(words, max_segment_words=5)
        self.status_label.configure(text="Generating subtitled video...")
        self.status_label.grid()
        self.progress_bar.grid()
        self.progress_bar.start()
        processed_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        processed_video.close()
        create_subtitled_video(
            self.input_video,
            processed_video.name,
            segments
        )
        add_movie_audio(self.input_video, processed_video.name, filename)
        os.remove(processed_video.name)
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.status_label.grid_remove()
        self.enable_buttons()


class TranscriptionWorker(threading.Thread):
    def __init__(self, transcribe_queue, model, filename, **transcribe_kwargs):
        self.queue = transcribe_queue
        self.model = model
        self.filename = filename
        self.transcribe_kwargs = transcribe_kwargs
        super().__init__()

    def run(self):
        words = transcribe_with_timestamps(self.model, self.filename, **self.transcribe_kwargs)
        self.queue.put(words)


def run_app():
    """Entrypoint for executable."""
    app = App()
    app.mainloop()
