#!/usr/bin/env python3

"""
Audio recorder module for Claude Voice TUI wrapper
"""

import pyaudio
import wave
import threading
import io
import numpy as np


class AudioRecorder:
    """Audio recorder that captures microphone input"""
    
    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.frames = []
        self.thread = None
        
    def _record_thread(self):
        """Thread function that captures audio data"""
        while self.recording:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            self.frames.append(data)
    
    def start(self):
        """Start recording audio"""
        if self.recording:
            return
            
        self.frames = []
        self.recording = True
        
        # Open audio stream
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        # Start recording thread
        self.thread = threading.Thread(target=self._record_thread)
        self.thread.start()
    
    def stop(self):
        """Stop recording and return audio data"""
        if not self.recording:
            return None
            
        self.recording = False
        
        # Wait for recording thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join()
        
        # Close audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Convert frames to audio data format expected by faster-whisper
        if self.frames:
            audio_data = b''.join(self.frames)
            # Convert to numpy array of float32 values normalized to [-1, 1]
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            return audio_np
        
        return None
    
    def __del__(self):
        """Cleanup resources"""
        if self.recording:
            self.stop()
        if hasattr(self, 'audio'):
            self.audio.terminate()