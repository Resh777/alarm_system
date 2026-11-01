import os
import threading
import subprocess
import platform

# Use winsound for Windows stability
if platform.system() == "Windows":
    import winsound
else:
    winsound = None

def trigger_alarm(title, context, priority=3):
    try:
        # 1. Visual Notification via PowerShell (Native Windows)
        def show_powershell_toast():
            try:
                # This PowerShell script creates a system tray notification
                # It uses the system-default icon and is very stable
                ps_script = f"""
                [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');
                $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon;
                $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information;
                $objNotifyIcon.BalloonTipIcon = 'Info';
                $objNotifyIcon.BalloonTipText = 'Task: {title}';
                $objNotifyIcon.BalloonTipTitle = 'Priority {priority} Alarm';
                $objNotifyIcon.Visible = $True;
                $objNotifyIcon.ShowBalloonTip(10000);
                """
                # Run the script hidden in the background
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
            except Exception as e:
                print(f"[NOTIFY ERROR] PowerShell toast failed: {e}")

        # Start the notification in its own thread
        threading.Thread(target=show_powershell_toast, daemon=True).start()

        # 2. Sound Logic
        sound_file = f"p{priority}.wav"
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sound_path = os.path.join(base_dir, "assets", "sounds", sound_file)

        if not os.path.exists(sound_path):
            print(f"[FILE ERROR] Missing sound: {sound_path}")
            return

        def play_sound():
            try:
                if platform.system() == "Windows" and winsound:
                    # SND_FILENAME plays the file, SND_ASYNC prevents freezing
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"[AUDIO ERROR] {e}")

        threading.Thread(target=play_sound, daemon=True).start()

    except Exception as global_err:
        print(f"[CRITICAL] {global_err}")