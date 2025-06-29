📬 Gmail Watcher - Email Notification Tool

Gmail Watcher is a simple tool that monitors your Gmail inbox for unread emails from specific senders and shows Windows notifications whenever a matching email arrives.

It works silently in the background and can be configured to start automatically with your Windows machine.

🚀 Features

✅ Real-time email checking every 15 seconds.

✅ Native Windows 10/11 toast notifications.

✅ Runs silently in background.

✅ Supports auto-start at Windows boot.

✅ Customizable target email senders via .env file.

✅ Packaged as .exe (no terminal shown)

✅ Works after system wake-up or boot

🛠️ Setup Instructions (Step-by-Step)

📌 1️⃣ Requirements

Google Account with Gmail.

Windows 10 or 11.

Python 3.10 (if compiling yourself)

📌 2️⃣ Google Cloud Setup (First Time Only)

Go to Google Cloud Console

Create a new project.

Enable Gmail API for the project.

Go to OAuth consent screen, choose external, and fill in app info (you can skip scopes for now).

Go to Credentials > Create Credentials > OAuth Client ID.

Choose Desktop App

Download the credentials.json file and place it in the same folder as the .exe

📌 3️⃣ Create .env file

Create a file named .env in the same folder as the executable:

TARGET_SENDERS=example1@gmail.com, example2@gmail.com

Add Gmail addresses you want to monitor (comma-separated).

📌 4️⃣ Run for the First Time

Double-click gmail_watcher.exe

Your browser will open asking for Gmail permission.

After logging in, token.json will be created in the folder.

From now on, the app will run silently and show notifications.

⚙️ Optional: Run on Windows Startup

Press Win + R → type shell:startup

Create a shortcut to your gmail_watcher.exe in that folder.

Set Start In folder in shortcut properties to the folder where your .exe is located.
🌐 Build the Executable 
Install required packages:pip install pyinstaller google-api-python-client google-auth google-auth-oauthlib python-dotenv pywin32

Use PyInstaller to compile::pyinstaller --noconsole --onefile --add-data "credentials.json;." --add-data ".env;." gmail_watcher.py

setup .exe file on startup  task schedular

