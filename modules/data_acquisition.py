import requests
import json

with open('config.json') as f:
    config = json.load(f)

def get_user_context():
    # Default values in case of API failure
    context = {
        "is_busy": False, 
        "weather_delay": False, 
        "temp": "--", 
        "condition": "Unknown",
        "city": config.get("city", "City")
    }
    
    api_key = config.get("weather_api_key")
    city = config.get("city")
    # units=metric gives us Celsius
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        res = requests.get(url, timeout=5).json()
        if res.get("cod") == 200:
            weather_main = res['weather'][0]['main']
            context["temp"] = f"{int(res['main']['temp'])}°C"
            context["condition"] = weather_main
            # Set delay flag if it's raining or storming
            if 'Rain' in weather_main or 'Storm' in weather_main:
                context["weather_delay"] = True
    except Exception as e:
        print(f"[Context Error] {e}")
        
    return context