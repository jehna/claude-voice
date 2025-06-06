#!/usr/bin/env python3

"""
Audio listener module for Claude Voice TUI wrapper
"""

import threading
import logging
from RealtimeSTT import AudioToTextRecorder
from typing import Callable

logging.basicConfig(level=logging.ERROR)
logging.getLogger("RealtimeSTT").setLevel(logging.ERROR)
logging.getLogger("transcribe").setLevel(logging.ERROR)
logging.getLogger("faster_whisper").setLevel(logging.ERROR)
logging.getLogger("audio_recorder").setLevel(logging.ERROR)


class AudioListener:
    """Audio listener that captures speech and sends to terminal"""

    def __init__(self):
        self.recorder = None
        self.thread = None
        self.running = False
        self.callbacks = []

    def _audio_listener_thread(self):
        """Audio listening thread that captures speech and sends to terminal"""
        try:
            self.recorder = AudioToTextRecorder(
                model="tiny.en",
                language="en",
                compute_type="float32",
                post_speech_silence_duration=1.2,
                enable_realtime_transcription=False,
                spinner=False,
                print_transcription_time=False,
                level=logging.CRITICAL,
                no_log_file=True,
                debug_mode=False,
            )

            while self.running:
                try:
                    def transcription_callback(text):
                        if text and self.running:
                            for callback in self.callbacks:
                                callback(text)

                    self.recorder.text(transcription_callback)

                except Exception as e:
                    logging.error(f"Error in audio processing: {e}")
                    if not self.running:
                        break

        except Exception as e:
            logging.error(f"Error initializing audio recorder: {e}")

    def start(self):
        """Start the audio listener in a separate thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._audio_listener_thread)
        self.thread.start()

    def stop(self):
        """Stop the audio listener"""
        self.recorder.stop()
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def add_transcription_callback(self, callback: Callable[[str], None]):
        """
        Add a callback function that gets called when output_buffer changes

        Args:
            callback: Function that takes the new output string as parameter
        """
        self.callbacks.append(callback)