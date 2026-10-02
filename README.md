# Task 1 - Voice Assistant

## Features
- Microphone speech recognition
- Text-to-speech responses
- Greeting, date and time
- Web search
- Weather API integration
- Timed audible reminders
- Small local knowledge base
- Custom commands stored in `commands.json`
- Optional SMTP email support

## Install
```bash
python -m pip install -r requirements.txt
```

On Windows, `SpeechRecognition[audio]` installs the microphone dependency. On Linux/macOS, follow the SpeechRecognition/PyAudio installation instructions for your platform.

## Run
```bash
python voice_assistant.py
```

## Optional environment variables
```text
OPENWEATHER_API_KEY=your_key
ASSISTANT_EMAIL=your_test_account@example.com
ASSISTANT_EMAIL_PASSWORD=your_app_password
ASSISTANT_SMTP_HOST=smtp.gmail.com
ASSISTANT_SMTP_PORT=587
```

Never commit real passwords or API keys to source control.

## Example commands
- "Hello"
- "What time is it?"
- "What is today's date?"
- "Search for Python tutorials"
- "Weather in Bengaluru"
- "Remind me to drink water in 30 seconds"
- "Add command open portfolio = Opening your portfolio command."

## Privacy
The microphone is accessed only while `listen()` is active. Speech recognition in this implementation uses Google's recognition service through SpeechRecognition, so spoken audio may be transmitted to that service. Weather requests send the requested city and API key to OpenWeatherMap. Email credentials are read from environment variables and are not written to disk by this program. Custom commands are stored locally in `commands.json`.
