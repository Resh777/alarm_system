import tkinter as tk
import threading
import time
from database import init_db
from modules.ui import AlarmApp
from modules.alarm_decision import check_alarms

def alarm_loop():
    while True:
        try:
            check_alarms()
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(15) # Check every 15 seconds

if __name__ == "__main__":
    init_db()
    
    # Start background thread for non-blocking performance
    threading.Thread(target=alarm_loop, daemon=True).start()
    
    root = tk.Tk()
    app = AlarmApp(root)
    root.mainloop()