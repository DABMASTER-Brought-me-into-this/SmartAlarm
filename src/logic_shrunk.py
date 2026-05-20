import os
import subprocess
# Environmental Variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ['OMP_NUM_THREADS'] = '1'
current_pid = os.getpid()

# Rest of the imports
import time
import random
import platform
import numpy as np
from neuralnetwork_shrunk import forward_pass, finetune
from custom import collect_audio_features, play_alarm_sound, get_resource_path, stop_alarm_sound
from datetime import datetime, timedelta


# Smart Alarm Logic
class SmartAlarmLogic:
  def __init__(self, hours=7, minutes=0):
    # Setting Wake Up End & Start Times
    now = datetime.now()  # Getting Time Now
    self.wue = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    # Checking If Alarm is in Past or Future
    if self.wue < now:
      self.wue += timedelta(days=1)  # Adding a day if it is in the past
    self.wus = self.wue - timedelta(minutes=30)  # Creating the 30 minutes window
    self.ema = 0.1
    self.emvar = 0.0
    self.alpha = 0.1
    self.emsd = self.emvar ** 0.5


  def run_alarm(self, stop_event, snoozing_event, data_queue):
    try:
      ##Neural Network Loading + Inference Mode

      ## Getting the Time Frame & Sleeping Till Then
      # Printing Alarm Out
      print(f"Alarm Set for {self.wus} - {self.wue}")
      time.sleep(5)

      # Building the CSV for Telemetry Logging
      fieldnames = ["Timestamp", "Raw_Probability", "Current_EMA", "Current_Threshold", "Triggered_Alarm"]
      sleep_data = []

      # Putting it to sleep
      system = platform.system()

      if system == "Darwin":  # macOS
        # Keep system awake while this process exists, then turn off screen
        current_pid = os.getpid()
        subprocess.Popen(['caffeinate', '-i', '-w', str(current_pid)])
        os.system("pmset displaysleepnow")

      elif system == "Windows":
        import ctypes
        # 1. 'Caffeinate' the CPU (ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        # This keeps the computer from hibernating even if the screen is off.
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)

        # 2. Turn off the monitor immediately
        # SendMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, POWER_OFF)
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)

      elif system == "Linux":
        # Linux is varied, but 'xset' is the most common tool for X11 sessions
        try:
          # Prevent system sleep (idle)
          subprocess.Popen(['systemd-inhibit', '--why="Alarm Running"', '--what=idle', 'sleep', 'infinity'])
          # Force monitor off
          subprocess.run(["xset", "dpms", "force", "off"])
        except FileNotFoundError:
          print("Linux power tools (xset/systemd-inhibit) not found.")
      # Sleeping Till Wake-up period
      now = datetime.now()
      if now < self.wus:
        time_to_sleep = (self.wus - now).total_seconds()
        stop_event.wait(timeout=time_to_sleep)

      counter = 0
      count_threshold = 10
      # Running Code Continuously Until Time Frame Exceeded
      while True:
        while now <= self.wue:
          if stop_event.is_set():
            stop_alarm_sound()
            return 0
          if snoozing_event.is_set():
            self.wue += timedelta(minutes=10)
            self.wus += timedelta(minutes=10)
            snoozing_event.clear()
            continue

          now = datetime.now()
          print("AUDIO COLLECTED")
          x = np.asarray(collect_audio_features(), dtype=np.float32).reshape(-1)
          x = forward_pass(x)
          print(f"{now.time()} | P(User in Light Sleep) = {x}")

          # Checking if Light Sleep
          actual_threshold = max((self.ema + self.emsd * 2), 0)
          actual_threshold = min(0.7, actual_threshold)
          exceed_threshold = x >= actual_threshold

          # Data Logging
          self.emvar = (1 - self.alpha) * (self.emvar + self.alpha * (x - self.ema) ** 2)
          self.emsd = self.emvar ** 0.5
          self.ema = self.ema * (1 - self.alpha) + x * self.alpha
          sleep_data.append([now.time(), x, self.ema, actual_threshold, exceed_threshold])
          data_queue.put([now, x, self.ema, actual_threshold])
          time.sleep(0.5)

          # Preventing Alarm from Trigger First 10 Runs
          counter += 1
          if counter < count_threshold:
            continue

          # Running Alarm if in Light Sleep
          if exceed_threshold:
            play_alarm_sound()
            while True:
              if stop_event.is_set():
                stop_alarm_sound()
                return 0
              if snoozing_event.is_set():
                stop_alarm_sound()
                self.wue += timedelta(minutes=10)
                self.wus += timedelta(minutes=10)
                snoozing_event.clear()
                break

        # Play Alarm if time period has passed
        play_alarm_sound()
        while True:
          if stop_event.is_set():
            stop_alarm_sound()
            return 0
          if snoozing_event.is_set():
            stop_alarm_sound()
            self.wue += timedelta(minutes=10)
            self.wus += timedelta(minutes=10)
            snoozing_event.clear()
            break

    except Exception as e:
      print(e)

  def fine_tune(self, df, l=0):
    # Accessing the Dataset
    ls = df[-1]
    df = df[:, :-1]

    # Seperating & formatting the inputs/outputs
    X = df.tolist()
    Y = ls.tolist()

    # Shuffling the dataset
    combined = list(zip(X, Y))
    random.shuffle(combined)
    X[:], Y[:] = zip(*combined)

    # Reformatting it as a Tensor
    X = np.asarray(X, dtype=np.float32)
    Y = np.asarray(Y, dtype=np.float32).reshape(-1, 1)

    finetune(X, Y)


if __name__ == "__main__":
  import threading
  import queue
  from datetime import datetime, timedelta

  # 1. Set the target time 5 minutes from right now
  # This guarantees we land squarely inside your 30-minute tracking window immediately
  target_time = datetime.now() + timedelta(minutes=5)
  print(f"=== Command Line Diagnostic Mode ===")
  print(f"Current Time: {datetime.now().time()}")
  print(f"Target Wake Up Time: {target_time.strftime('%H:%M:%S')}")

  # 2. Instantiate the logic engine directly
  engine = SmartAlarmLogic(hours=target_time.hour, minutes=target_time.minute)

  # 3. Create the multi-threading synchronization events manually
  stop_event = threading.Event()
  snooze_event = threading.Event()
  data_queue = queue.Queue()

  # 4. Run the loop blocking on the main thread so crashes hit our screen
  engine.run_alarm(stop_event, snooze_event, data_queue)