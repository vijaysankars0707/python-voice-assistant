import datetime as dt
import json
import os
import re
import smtplib
import threading
import time
import webbrowser
from email.message import EmailMessage
from urllib.parse import quote_plus

import pyttsx3
import requests
import speech_recognition as sr

CONFIG_FILE = "commands.json"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

engine = pyttsx3.init()
recognizer = sr.Recognizer()
stop_event = threading.Event()


def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()


def listen():
    try:
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
        return recognizer.recognize_google(audio).strip()
    except sr.WaitTimeoutError:
        speak("I did not hear anything. Please try again.")
    except sr.UnknownValueError:
        speak("I could not understand that. Please repeat.")
    except sr.RequestError:
        speak("The speech recognition service is unavailable right now.")
    except Exception as exc:
        print("Microphone error:", exc)
        speak("There was a microphone error. Please check your microphone.")
    return ""


def load_custom_commands():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_custom_command(trigger, response):
    commands = load_custom_commands()
    commands[trigger.lower()] = response
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2)


def weather(city):
    if not OPENWEATHER_API_KEY:
        return "Weather is not configured. Set the OPENWEATHER_API_KEY environment variable."
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        data = requests.get(
            url,
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=10,
        ).json()
        if data.get("cod") != 200:
            return f"I could not find weather for {city}."
        condition = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        return f"In {city}, it is {temp:.1f} degrees Celsius with {condition}. Humidity is {humidity} percent and wind speed is {wind} meters per second."
    except requests.RequestException:
        return "I could not reach the weather service."


def send_email(to_address, subject, body):
    user = os.getenv("ASSISTANT_EMAIL")
    password = os.getenv("ASSISTANT_EMAIL_PASSWORD")
    smtp_host = os.getenv("ASSISTANT_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("ASSISTANT_SMTP_PORT", "587"))
    if not user or not password:
        return "Email is not configured. Set ASSISTANT_EMAIL and ASSISTANT_EMAIL_PASSWORD."
    try:
        msg = EmailMessage()
        msg["From"] = user
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return "The email was sent successfully."
    except Exception as exc:
        print("Email error:", exc)
        return "I could not send the email. Check the SMTP settings."


def reminder_worker(seconds, message):
    time.sleep(seconds)
    if not stop_event.is_set():
        speak(f"Reminder: {message}")


def parse_duration(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(seconds?|minutes?|hours?)", text.lower())
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    multiplier = 3600 if unit.startswith("hour") else 60 if unit.startswith("minute") else 1
    return int(value * multiplier)


def handle_command(command):
    text = command.lower().strip()
    custom = load_custom_commands()

    for trigger, response in custom.items():
        if trigger in text:
            return response

    if any(x in text for x in ("hello", "hi assistant", "hey assistant")):
        return "Hello! How can I help you?"

    if any(x in text for x in ("time", "what time")):
        return dt.datetime.now().strftime("The current time is %I:%M %p.")

    if any(x in text for x in ("date", "what day")):
        return dt.datetime.now().strftime("Today is %A, %B %d, %Y.")

    if text in ("quit", "exit", "goodbye", "stop"):
        return "__EXIT__"

    if text.startswith("search ") or "search for " in text:
        query = text.split("search ", 1)[-1]
        if "search for " in text:
            query = text.split("search for ", 1)[1]
        if query.strip():
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(query))
            return f"I opened a web search for {query}."

    if text.startswith("weather in "):
        city = command[11:].strip()
        return weather(city)

    if text.startswith("weather "):
        city = command[8:].strip()
        return weather(city)

    duration = parse_duration(text)
    if "remind me" in text and duration:
        message = re.sub(r"remind me( to)?", "", command, flags=re.I)
        message = re.sub(r"\d+(?:\.\d+)?\s*(seconds?|minutes?|hours?)", "", message, flags=re.I)
        message = message.strip(" ,.")
        threading.Thread(target=reminder_worker, args=(duration, message or "your reminder"), daemon=True).start()
        return f"Okay. I will remind you in {duration} seconds."

    if text.startswith("add command"):
        # Example: "add command open my portfolio = opening your portfolio"
        if "=" in command:
            left, right = command.split("=", 1)
            trigger = left.replace("add command", "", 1).strip()
            response = right.strip()
            if trigger and response:
                try:
                    save_custom_command(trigger, response)
                    return f"Custom command '{trigger}' saved."
                except OSError:
                    return "I could not save the custom command."
        return "Say: add command trigger equals response."

    if text.startswith("send email"):
        return ("For safety, email sending is implemented as a function but requires "
                "configured environment variables. Use send_email(to, subject, body) from the code.")

    # Simple local knowledge base for general knowledge.
    knowledge = {
        "capital of france": "The capital of France is Paris.",
        "capital of india": "The capital of India is New Delhi.",
        "python": "Python is a general-purpose programming language known for readable syntax.",
        "who created python": "Python was created by Guido van Rossum and first released in 1991.",
    }
    for question, answer in knowledge.items():
        if question in text:
            return answer

    return "I do not know that yet. Try asking for the time, date, weather, a web search, or a reminder."


def main():
    speak("Voice assistant started. Say hello, ask for the time, weather, or a web search. Say goodbye to exit.")
    while True:
        command = listen()
        if not command:
            continue
        print("You:", command)
        response = handle_command(command)
        if response == "__EXIT__":
            speak("Goodbye!")
            break
        speak(response)


if __name__ == "__main__":
    main()
