import tkinter as tk
from tkinter import ttk, messagebox
from database import add_alarm, get_pending_alarms
from modules.nlp_context import parse_alarm_text
from modules.data_acquisition import get_user_context

class AlarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Smart Alarm & Weather Hub")
        self.root.geometry("600x750") 
        self.root.configure(bg="#f5f5f5")

        # --- WEATHER DASHBOARD ---
        self.weather_frame = tk.Frame(root, bg="#2c3e50", pady=15)
        self.weather_frame.pack(fill="x")

        self.city_lbl = tk.Label(self.weather_frame, text="Loading City...", font=("Arial", 12), fg="#ecf0f1", bg="#2c3e50")
        self.city_lbl.pack()

        self.temp_lbl = tk.Label(self.weather_frame, text="--°C", font=("Arial", 32, "bold"), fg="white", bg="#2c3e50")
        self.temp_lbl.pack()

        self.cond_lbl = tk.Label(self.weather_frame, text="Checking weather...", font=("Arial", 10, "italic"), fg="#bdc3c7", bg="#2c3e50")
        self.cond_lbl.pack()

        # --- NLP INPUT SECTION ---
        nlp_frame = tk.LabelFrame(root, text="Smart Alarm Command", padx=10, pady=10, bg="#f5f5f5")
        nlp_frame.pack(pady=15, fill="x", padx=20)
        
        # Text Entry
        self.nlp_ent = tk.Entry(nlp_frame, width=30, font=("Arial", 11))
        self.nlp_ent.pack(side="left", padx=5)
        self.nlp_ent.insert(0, "Wake me up at 7 AM (urgent)") 

        # Priority Selector (Manually set priority)
        tk.Label(nlp_frame, text="Prio:", bg="#f5f5f5", font=("Arial", 9)).pack(side="left", padx=2)
        self.prio_combo = ttk.Combobox(nlp_frame, values=[1, 3, 5], width=3, state="readonly")
        self.prio_combo.set(3) # Default to P3
        self.prio_combo.pack(side="left", padx=5)
        
        tk.Button(nlp_frame, text="Add", command=self.add_nlp_alarm, 
                  bg="#3498db", fg="white", relief="flat", padx=10).pack(side="left")

        # --- GOOGLE CALENDAR SYNC SECTION ---
        self.sync_btn = tk.Button(root, text="Sync Google Calendar Events", 
                                  command=self.sync_calendar, bg="#e67e22", fg="white", 
                                  font=("Arial", 10, "bold"), pady=8, relief="flat")
        self.sync_btn.pack(pady=5, fill="x", padx=20)

        # --- ALARM LIST SECTION ---
        list_frame = tk.Frame(root, bg="#f5f5f5")
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, text="Upcoming Alarms", font=("Arial", 10, "bold"), bg="#f5f5f5").pack(anchor="w")
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Title", "Time", "Prio"), show='headings')
        for col in ("ID", "Title", "Time", "Prio"): 
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(pady=5, fill="both", expand=True)

        # Initial data load
        self.refresh_weather()
        self.refresh_list()

    def refresh_weather(self):
        """Updates the top weather display from the API."""
        try:
            ctx = get_user_context()
            self.city_lbl.config(text=ctx["city"].upper())
            self.temp_lbl.config(text=ctx["temp"])
            self.cond_lbl.config(text=ctx["condition"])
        except Exception as e:
            print(f"UI Weather Update Error: {e}")
        self.root.after(600000, self.refresh_weather)

    def sync_calendar(self):
        """Triggers the Google Calendar sync logic."""
        try:
            from modules.alarm_decision import sync_calendar_to_alarms
            self.sync_btn.config(text="Syncing...", state="disabled")
            self.root.update_idletasks() 

            sync_calendar_to_alarms()
            
            self.refresh_list()
            self.sync_btn.config(text="Sync Google Calendar Events", state="normal")
            messagebox.showinfo("Calendar Sync", "Successfully fetched events!")
        except Exception as e:
            self.sync_btn.config(text="Sync Google Calendar Events", state="normal")
            messagebox.showerror("Sync Error", f"Failed to sync calendar: {e}")

    def add_nlp_alarm(self):
        """Extracts data from UI/NLP and saves to Database."""
        text = self.nlp_ent.get()
        
        # Step 1: Parse the text using NLP
        # Note: Make sure you updated parse_alarm_text to return (time, task, cond, nlp_prio)
        parsed_data = parse_alarm_text(text)
        
        # Standardizing return to handle both old and new parse_alarm_text versions
        if len(parsed_data) == 4:
            time_val, task, cond, nlp_prio = parsed_data
        else:
            time_val, task, cond = parsed_data
            nlp_prio = 3

        if time_val:
            # Step 2: Determine priority
            # Priority Logic: Use manual dropdown UNLESS NLP detected "urgent/low" keywords
            manual_prio = int(self.prio_combo.get())
            final_prio = nlp_prio if nlp_prio != 3 else manual_prio

            # Step 3: Add to DB
            add_alarm(task, time_val, final_prio, cond) 
            self.refresh_list()
            
            self.nlp_ent.delete(0, tk.END)
            msg = f"Alarm set for {time_val} (Priority P{final_prio})"
            if cond:
                msg += f" \nCondition: {cond}"
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("NLP Error", "Could not understand the time. Please use 'HH:MM AM/PM' format.")

    def refresh_list(self):
        """Refreshes the Treeview with latest data from DB."""
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        for row in get_pending_alarms():
            self.tree.insert("", "end", values=(row[0], row[1], row[2], f"P{row[3]}"))