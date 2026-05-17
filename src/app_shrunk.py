import customtkinter as ctk
import threading
import queue
import numpy as np
import custom
import logic_shrunk as logic
import sounddevice as sd

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")


class SmartAlarmUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Alarm")
        self.geometry("600x550")
        self.resizable(False, False)

        self.trigger_mic_permission()

        self.alarm_thread = None
        self.stop_event = threading.Event()
        self.snooze_event = threading.Event()
        self.data_queue = queue.Queue()
        self.graph_data = {"time": [], "prob": [], "ema": [], "thresh": []}

        self.setup_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_frame.pack(fill="both", expand=True)

        self.dashboard_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.build_setup_ui()
        self.build_dashboard_ui()

        self.bind_all("<Button-1>", self.remove_focus)

    def trigger_mic_permission(self):
        """Silently opens and closes the mic to force the macOS permission pop-up."""
        try:
            stream = sd.InputStream(samplerate=16000, channels=1)
            stream.start()
            stream.stop()
            stream.close()
        except Exception as e:
            print(f"Mic init: {e}")

    def remove_focus(self, event):
        try:
            if event.widget.winfo_class() not in ['Entry', 'TEntry']:
                self.focus_set()
        except Exception:
            pass

    def adjust_hour(self, delta):
        try:
            current = int(self.hour_var.get())
        except ValueError:
            current = 7
        current += delta
        if current > 12:
            current = 1
        elif current < 1:
            current = 12
        self.hour_var.set(f"{current:02d}")

    def adjust_minute(self, delta):
        try:
            current = int(self.minute_var.get())
        except ValueError:
            current = 0
        current += delta
        if current > 59:
            current = 0
        elif current < 0:
            current = 59
        self.minute_var.set(f"{current:02d}")

    def build_setup_ui(self):
        ctk.CTkLabel(self.setup_frame, text="WAKE UP TIME", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="gray").pack(pady=(60, 10))

        time_frame = ctk.CTkFrame(self.setup_frame, fg_color="#1e1e1e", corner_radius=15)
        time_frame.pack(pady=10, padx=80, fill="x")

        inner_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        inner_frame.pack(pady=20)

        self.hour_var = ctk.StringVar(value="07")
        self.minute_var = ctk.StringVar(value="00")

        hour_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        hour_frame.pack(side="left", padx=10)
        ctk.CTkButton(hour_frame, text="▲", width=50, fg_color="transparent", hover_color="#333333",
                      command=lambda: self.adjust_hour(1)).pack()

        hour_entry = ctk.CTkEntry(hour_frame, textvariable=self.hour_var, font=ctk.CTkFont(size=50, weight="bold"),
                                  width=80, justify="center", border_width=0, fg_color="transparent",
                                  text_color="white")
        hour_entry.pack(pady=5)

        ctk.CTkButton(hour_frame, text="▼", width=50, fg_color="transparent", hover_color="#333333",
                      command=lambda: self.adjust_hour(-1)).pack()

        ctk.CTkLabel(inner_frame, text=":", font=ctk.CTkFont(size=50, weight="bold"), text_color="#42A5F5").pack(
            side="left", padx=5)

        minute_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        minute_frame.pack(side="left", padx=10)
        ctk.CTkButton(minute_frame, text="▲", width=50, fg_color="transparent", hover_color="#333333",
                      command=lambda: self.adjust_minute(1)).pack()

        minute_entry = ctk.CTkEntry(minute_frame, textvariable=self.minute_var,
                                    font=ctk.CTkFont(size=50, weight="bold"),
                                    width=80, justify="center", border_width=0, fg_color="transparent",
                                    text_color="white")
        minute_entry.pack(pady=5)

        ctk.CTkButton(minute_frame, text="▼", width=50, fg_color="transparent", hover_color="#333333",
                      command=lambda: self.adjust_minute(-1)).pack()

        self.ampm_var = ctk.StringVar(value="AM")
        ampm_toggle = ctk.CTkSegmentedButton(self.setup_frame, variable=self.ampm_var, values=["AM", "PM"],
                                             width=200, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        ampm_toggle.pack(pady=20)

        ctk.CTkButton(self.setup_frame, text="INITIATE SLEEP TRACKING", height=50, width=250,
                      font=ctk.CTkFont(size=14, weight="bold"), command=self.start_alarm).pack(pady=20)

        ctk.CTkButton(self.setup_frame, text="⚙️ Calibrate Room Acoustics", fg_color="transparent",
                      hover_color="#2b2b2b", text_color="gray", command=self.open_calibration_wizard).pack(
            side="bottom", pady=20)

    def build_dashboard_ui(self):
        self.status_label = ctk.CTkLabel(self.dashboard_frame, text="● LIVE SLEEP ARCHITECTURE",
                                         font=ctk.CTkFont(size=16, weight="bold"), text_color="#66BB6A")
        self.status_label.pack(pady=(30, 10))

        # --- NATIVE TKINTER CANVAS GRAPH ENGINE ---
        self.canvas = ctk.CTkCanvas(self.dashboard_frame, bg='#242424', highlightthickness=0, height=220)
        self.canvas.pack(pady=10, padx=30, fill="both", expand=True)

        btn_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(btn_frame, text="Snooze (10m)", height=45, width=140, fg_color="#E59500",
                      hover_color="#C07C00", font=ctk.CTkFont(weight="bold"), command=self.snooze).pack(side="left",
                                                                                                        padx=10)
        ctk.CTkButton(btn_frame, text="Stop Alarm", height=45, width=140, fg_color="#D32F2F",
                      hover_color="#9A0007", font=ctk.CTkFont(weight="bold"), command=self.stop_alarm).pack(side="left",
                                                                                                            padx=10)

    def open_calibration_wizard(self):
        self.cal_window = ctk.CTkToplevel(self)
        self.cal_window.title("Calibration Wizard")
        self.cal_window.geometry("400x350")
        self.cal_window.attributes('-topmost', 'true')

        ctk.CTkLabel(self.cal_window, text="Acoustic Calibration", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=15)
        ctk.CTkLabel(self.cal_window,
                     text="1. Ensure room is silent.\n2. When prompted, move on bed.\n3. Click 'Record Baseline'.",
                     wraplength=300, text_color="gray").pack(pady=5)

        self.cal_dur_var = ctk.StringVar(value="60s")
        self.dur_toggle = ctk.CTkSegmentedButton(self.cal_window, variable=self.cal_dur_var,
                                                 values=["30s", "60s", "120s", "Custom"],
                                                 command=self.toggle_custom_dur)
        self.dur_toggle.pack(pady=10)

        self.custom_dur_entry = ctk.CTkEntry(self.cal_window, placeholder_text="Seconds (e.g. 45)", justify="center")

        self.cal_btn = ctk.CTkButton(self.cal_window, text="Record Baseline", height=40,
                                     command=self.run_calibration_thread)
        self.cal_btn.pack(pady=10)

        self.cal_status_label = ctk.CTkLabel(self.cal_window, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self.cal_status_label.pack(pady=20)

        # Hidden Resume Button
        self.ready_btn = ctk.CTkButton(self.cal_window, text="OK, I'm Ready", height=40, fg_color="#E59500",
                                       hover_color="#C07C00", font=ctk.CTkFont(weight="bold"),
                                       command=self.resume_calibration)

        self.move_event = threading.Event()

    def toggle_custom_dur(self, value):
        if value == "Custom":
            self.custom_dur_entry.pack(pady=5, before=self.cal_btn)
        else:
            self.custom_dur_entry.pack_forget()

    def run_calibration_thread(self):
        if self.cal_dur_var.get() == "Custom":
            try:
                total_seconds = int(self.custom_dur_entry.get())
            except ValueError:
                total_seconds = 60
        else:
            total_seconds = int(self.cal_dur_var.get().split("s")[0])

        len_time = max(1, total_seconds // 3)
        self.real_seconds = len_time * 3
        self.halfway_mark = self.real_seconds // 2

        # Clean the UI for the timer
        self.cal_btn.configure(state="disabled")
        self.cal_btn.pack_forget()
        self.dur_toggle.pack_forget()
        self.custom_dur_entry.pack_forget()

        self.move_event.clear()

        # Pass the move_event to the backend
        threading.Thread(target=self.execute_calibration, args=(len_time,), daemon=True).start()

        self.countdown_timer()

    def countdown_timer(self):
        if self.real_seconds <= 0:
            self.cal_status_label.configure(text="✅ Fine-Tuning Complete!", text_color="#66BB6A")
            self.cal_btn.configure(state="normal", text="Record Again")
            self.dur_toggle.pack(pady=10, before=self.cal_status_label)
            if self.cal_dur_var.get() == "Custom":
                self.custom_dur_entry.pack(pady=5, before=self.cal_status_label)
            self.cal_btn.pack(pady=10, before=self.cal_status_label)
            return

        # THE MIDPOINT TRAP
        if self.real_seconds == self.halfway_mark and not self.move_event.is_set():
            self.cal_status_label.configure(text="Now get ready to move on your bed.", text_color="#E59500",
                                            font=ctk.CTkFont(size=16, weight="bold"))
            self.ready_btn.pack(pady=10)
            return  # Freeze the UI timer loop until they click the button

        if self.real_seconds > self.halfway_mark:
            phase_time = self.real_seconds - self.halfway_mark
            self.cal_status_label.configure(text=f"🤫 SILENT PHASE: {phase_time}s", text_color="#42A5F5",
                                            font=ctk.CTkFont(size=20, weight="bold"))
        else:
            self.cal_status_label.configure(text=f"🐒 MONKEY MODE: {self.real_seconds}s", text_color="#E59500",
                                            font=ctk.CTkFont(size=20, weight="bold"))

        self.real_seconds -= 1
        self.after(1000, self.countdown_timer)

    def resume_calibration(self):
        self.ready_btn.pack_forget()
        self.move_event.set()  # Unfreezes custom.py backend
        self.countdown_timer()  # Resumes the UI loop

    def execute_calibration(self, len_time):
        try:
            raw_data = []

            # Phase 1: Silent Phase (Room Noise -> Label 0)
            half_iterations = max(1, len_time // 2)

            for _ in range(half_iterations):
                fv = custom.collect_audio_features()
                raw_data.append(fv.flatten().tolist() + [0])

            # Wait for user to click "Ready" and get on the bed
            self.move_event.wait()

            # Phase 2: Monkey Mode (Bed Sounds -> Label 1)
            for _ in range(half_iterations):
                fv = custom.collect_audio_features()
                raw_data.append(fv.flatten().tolist() + [1])

            # PURE NUMPY MATRIX FORMATTING (NO PANDAS)
            np_data = np.array(raw_data, dtype=np.float32)

            # Run Fine-Tuning
            temp_logic = logic.SmartAlarmLogic()
            temp_logic.fine_tune(np_data)

        except Exception as e:
            print(f"Calibration Backend Error: {e}")

    def start_alarm(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.minute_var.get())
            h = max(1, min(12, h))
            m = max(0, min(59, m))
            self.hour_var.set(f"{h:02d}")
            self.minute_var.set(f"{m:02d}")
        except ValueError:
            h, m = 7, 0
            self.hour_var.set("07")
            self.minute_var.set("00")

        if self.ampm_var.get() == "PM" and h != 12:
            h += 12
        elif self.ampm_var.get() == "AM" and h == 12:
            h = 0

        self.stop_event.clear()
        self.snooze_event.clear()
        self.graph_data = {"time": [], "prob": [], "ema": [], "thresh": []}

        self.setup_frame.pack_forget()
        self.dashboard_frame.pack(fill="both", expand=True)

        alarm_engine = logic.SmartAlarmLogic(h, m)
        self.alarm_thread = threading.Thread(
            target=alarm_engine.run_alarm,
            args=(self.stop_event, self.snooze_event, self.data_queue),
            daemon=True
        )
        self.alarm_thread.start()
        self.update_dashboard()

    def update_dashboard(self):
        if self.stop_event.is_set():
            return

        try:
            updated = False
            while not self.data_queue.empty():
                timestamp, x, ema, thresh = self.data_queue.get_nowait()

                prob_val = float(np.array(x).flatten()[0])
                ema_val = float(np.array(ema).flatten()[0])
                thresh_val = float(np.array(thresh).flatten()[0])

                self.graph_data["time"].append(timestamp.strftime("%H:%M:%S"))
                self.graph_data["prob"].append(prob_val)
                self.graph_data["ema"].append(ema_val)
                self.graph_data["thresh"].append(thresh_val)
                updated = True

                # Keep last 30 points
                if len(self.graph_data["time"]) > 30:
                    for key in self.graph_data:
                        self.graph_data[key].pop(0)

            # --- NATIVE TKINTER GRAPH DRAWING ---
            if updated:
                self.canvas.delete("all")

                # Force Tkinter to calculate accurate geometry dimensions
                self.canvas.update_idletasks()
                width = self.canvas.winfo_width()
                height = self.canvas.winfo_height()

                # Only draw if we have dimensions and at least 2 points to make a line
                if width > 1 and height > 1 and len(self.graph_data["prob"]) >= 2:
                    # 1. FAINT REFERENCE LINE
                    self.canvas.create_line(0, height / 2, width, height / 2, fill="#333333", dash=(2, 4))

                    # 2. FLOATING LEGEND
                    self.canvas.create_text(10, 15, text="— Raw", fill="#42A5F5", anchor="w",
                                            font=("Arial", 12, "bold"))
                    self.canvas.create_text(80, 15, text="— EMA", fill="#66BB6A", anchor="w",
                                            font=("Arial", 12, "bold"))
                    self.canvas.create_text(150, 15, text="-- Threshold", fill="#EF5350", anchor="w",
                                            font=("Arial", 12, "bold"))

                    # 3. DYNAMIC PIXEL MATH (Fixes the squishing bug)
                    data_length = len(self.graph_data["prob"])
                    x_step = width / max(1, data_length - 1)

                    def get_coords(data_list):
                        coords = []
                        for i, val in enumerate(data_list):
                            x_px = i * x_step
                            y_px = height - (val * height)
                            coords.extend([x_px, y_px])
                        return coords

                    prob_coords = get_coords(self.graph_data["prob"])
                    ema_coords = get_coords(self.graph_data["ema"])
                    thresh_coords = get_coords(self.graph_data["thresh"])

                    # 4. PLOT LINES
                    self.canvas.create_line(*prob_coords, fill="#42A5F5", width=3, smooth=True)
                    self.canvas.create_line(*ema_coords, fill="#66BB6A", width=3, smooth=True)
                    self.canvas.create_line(*thresh_coords, fill="#EF5350", width=2, dash=(5, 5))

        except queue.Empty:
            pass
        except Exception as e:
            print(f"Graph Render Error: {e}")

        self.after(500, self.update_dashboard)

    def snooze(self):
        self.snooze_event.set()
        try:
            custom.stop_alarm_sound()
        except:
            pass

    def stop_alarm(self):
        self.stop_event.set()
        try:
            custom.stop_alarm_sound()
        except:
            pass
        self.dashboard_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = SmartAlarmUI()
    app.mainloop()