import heapq
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from database import get_pending_alarms, update_alarm_status, log_action, add_alarm
from modules.notification import trigger_alarm
from modules.data_acquisition import get_user_context
from modules.calendar_sync import get_upcoming_events

# Technical Optimization: Non-blocking thread pool
executor = ThreadPoolExecutor(max_workers=4)

def check_alarms():
    """
    Evaluates pending alarms with Weather Gating, Intelligent Adjustment,
    and Priority-based Conflict Resolution.
    """
    raw_alarms = get_pending_alarms()
    context = get_user_context() # Returns {'condition': 'Clear', 'temp': '28C', 'weather_delay': False...}
    now = datetime.now()
    
    conflict_resolver = []

    for alarm in raw_alarms:
        # Unpack: (id, title, time, priority, condition_string)
        aid, title, time_str, prio, alarm_cond = alarm
        
        try:
            alarm_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            
            # --- 1. INTELLIGENT TIME ADJUSTMENT ---
            # If weather context indicates rain, Priority 1 alarms ring 5 mins early.
            if context.get("weather_delay") and prio == 1:
                alarm_dt -= timedelta(minutes=5)
            
            # --- 2. TRIGGER CHECK ---
            if now >= alarm_dt:
                should_trigger = True
                
                # --- 3. RECTIFICATION LOGIC (WEATHER GATING) ---
                # Checks if the alarm was set with a specific weather requirement
                if alarm_cond and alarm_cond not in ["calendar_auto", "none", "None"]:
                    # Compare current API weather with the alarm's requirement
                    current_weather = context.get("condition", "").lower()
                    required_weather = alarm_cond.lower()
                    
                    if required_weather != current_weather:
                        should_trigger = False
                        # Log the skip for debugging
                        print(f"[SKIPPED] Alarm {aid} ('{title}') waiting for {required_weather}. Current is {current_weather}.")
                
                # If all conditions pass, add to the priority heap
                if should_trigger:
                    heapq.heappush(conflict_resolver, (prio, alarm))
                    
        except Exception as e:
            print(f"[ERROR] Logic check failed for ID {aid}: {e}")
    # --- PRIORITY-AWARE RESOLVER ---
    while conflict_resolver:
        prio, alarm_data = heapq.heappop(conflict_resolver)
        aid, title, _, _, _ = alarm_data
        
        print(f"[RESOLVER] Triggering P{prio}: {title}")
        
        # Pass the 'prio' variable here -------------------v
        threading.Thread(
            target=trigger_alarm, 
            args=(title, context, prio), 
            daemon=True
        ).start()
        
        update_alarm_status(aid, "triggered")
        log_action(aid, f"Triggered (Priority {prio})")
    


def sync_calendar_to_alarms():
    """
    Scans Google Calendar and creates alarms with a buffer based on weather.
    """
    events = get_upcoming_events(max_results=1)
    context = get_user_context()
    
    if not events:
        print("[CALENDAR] No upcoming events found.")
        return

    event = events[0]
    start_str = event['start'].get('dateTime', event['start'].get('date'))
    
    # Standardize time for comparison
    event_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
    event_time = event_time.replace(tzinfo=None) 

    # Calculation: 60 mins base + 20 mins if weather is bad
    prep_time = 60 
    if context.get("weather_delay"):
        prep_time += 20
        print("[INTEL] Bad weather detected. Increasing prep buffer to 80 mins.")

    suggested_alarm_time = event_time - timedelta(minutes=prep_time)
    title = f"Meeting: {event['summary']}"
    
    # Add to DB with 'calendar_auto' tag to distinguish it from manual weather-gated alarms
    add_alarm(title, suggested_alarm_time.strftime("%Y-%m-%d %H:%M"), 1, "calendar_auto")
    print(f"[SUCCESS] Calendar alarm set for {title} at {suggested_alarm_time}")