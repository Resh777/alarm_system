import spacy
from datetime import datetime, timedelta

# Load the NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def parse_alarm_text(text):
    """
    Parses natural language to extract Time, Task Title, and Weather Conditions.
    Example: 'Wake me up at 12:45 PM if it is cloudy'
    """
    doc = nlp(text.lower())
    alarm_time = None
    condition = None  
    
    # 1. Detect Weather Keywords (Condition Logic)
    # We map common words to OpenWeatherMap standard condition strings
    if "cloudy" in text.lower() or "clouds" in text.lower():
        condition = "Clouds"
    elif "rain" in text.lower():
        condition = "Rain"
    elif "clear" in text.lower():
        condition = "Clear"
    elif "thunderstorm" in text.lower():
        condition = "Thunderstorm"

    # 2. Time Extraction Logic
    time_entities = [ent.text for ent in doc.ents if ent.label_ == "TIME"]
    
    if time_entities:
        raw_time = time_entities[0].upper().replace(".", "")
        try:
            # Try parsing common formats like '12:45 PM' or '7 AM'
            formats = ["%I:%M %p", "%I %p", "%H:%M"]
            parsed_t = None
            for fmt in formats:
                try:
                    parsed_t = datetime.strptime(raw_time, fmt)
                    break
                except:
                    continue
            
            if parsed_t:
                now = datetime.now()
                # Create a datetime for today with the parsed hours/minutes
                target_dt = now.replace(hour=parsed_t.hour, minute=parsed_t.minute, second=0, microsecond=0)
                
                # If the time has already passed today, set it for tomorrow
                if target_dt < now:
                    target_dt += timedelta(days=1)
                
                alarm_time = target_dt.strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            print(f"NLP Time Parsing Error: {e}")

    # 3. Task Title Extraction
    # Clean up the title by removing the time string and the condition keywords
    task = text
    if time_entities:
        task = task.replace(time_entities[0], "")
    
    # Optional: Clean up words like "if it is", "at", "on" for a cleaner title
    stop_phrases = ["if it is", "when it is", "at", "on", "cloudy", "rainy", "clear"]
    for phrase in stop_phrases:
        task = task.replace(phrase, "")
    
    task = task.strip().capitalize()
    if not task:
        task = "NLP Alarm"

    return alarm_time, task, condition
    # 4. Priority Extraction Logic
    priority = 3  # Default
    if any(word in text.lower() for word in ["urgent", "important", "emergency", "p1"]):
        priority = 1
    elif any(word in text.lower() for word in ["low", "casual", "whenever", "p5"]):
        priority = 5

    # Clean up priority words from the task title
    stop_phrases += ["urgent", "important", "low priority", "casual"]
    # ... (rest of your cleaning logic) ...

    return alarm_time, task, condition, priority # Return 4 values now