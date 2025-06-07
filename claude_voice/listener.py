#!/usr/bin/env python3

"""
Audio listener module for Claude Voice TUI wrapper
"""

import threading
import logging
from faster_whisper import WhisperModel
from typing import Callable
import time
from .audiorecorder import AudioRecorder
from enum import Enum

logging.basicConfig(level=logging.ERROR)
logging.getLogger("RealtimeSTT").setLevel(logging.ERROR)
logging.getLogger("transcribe").setLevel(logging.ERROR)
logging.getLogger("faster_whisper").setLevel(logging.ERROR)
logging.getLogger("audio_recorder").setLevel(logging.ERROR)

class Model(Enum):
    TINY = "tiny.en"
    BASE = "base.en"
    SMALL = "small.en"
    MEDIUM = "medium.en"
    LARGE = "large-v2"
    LARGE_V3 = "large-v3"

class AudioListener:
    """Audio listener that captures speech and sends to terminal"""

    def __init__(self, model: Model = Model.TINY):
        self.recorder = None
        self.thread = None
        self.running = False
        self.model = model
        self.callbacks = []

    def _audio_listener_thread(self):
        """Audio listening thread that captures speech and sends to terminal"""
        try:
            self.transcriber = WhisperModel(self.model.value, device="cpu", compute_type="int8")
            self.recorder = AudioRecorder()

        except Exception as e:
            logging.error(f"Error initializing audio recorder: {e}")

    def start(self):
        """Start the audio listener in a separate thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._audio_listener_thread)
        self.thread.start()

        while not self.recorder:
            time.sleep(0.1)

    def stop(self):
        """Stop the audio listener"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def sleep(self):
        """Put the listener into sleeping mode - stops processing transcriptions"""
        recording = self.recorder.stop()
        segments, info = self.transcriber.transcribe(recording)
        for callback in self.callbacks:
            callback("".join([segment.text for segment in segments]))

    def wake_up(self):
        """Wake up the listener from sleeping mode - resumes processing transcriptions"""
        self.recorder.start()


    def add_transcription_callback(self, callback: Callable[[str], None]):
        """
        Add a callback function that gets called when output_buffer changes

        Args:
            callback: Function that takes the new output string as parameter
        """
        self.callbacks.append(callback)