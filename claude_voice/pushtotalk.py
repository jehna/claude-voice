from .listener import AudioListener
from pynput import keyboard
from pynput.keyboard import KeyCode
import threading

class PushToTalk:
  def __init__(self, listener: AudioListener, hotkey: KeyCode = keyboard.Key.space):
    self.listener = listener
    self.hotkey = hotkey
    self.sleeping = True

  def start(self):
    self.thread = threading.Thread(target=self._start)
    self.thread.start()

  def _start(self):
    with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
        listener.join()

  def on_press(self, key):
    if key == self.hotkey:
      if self.sleeping:
        self.sleeping = False
        self.listener.wake_up()

  def on_release(self, key):
    if key == self.hotkey:
      if not self.sleeping:
        self.sleeping = True
        self.listener.sleep()
