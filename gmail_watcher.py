import os
import re
import sys
import time
import subprocess
import webbrowser
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.utils import parseaddr

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def log(message):
    log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
    log_path = os.path.join(log_dir, "watcher_log.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} - {message}\n")

def resource_path(relative_path):
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        full_path = os.path.join(base_path, relative_path)
        log(f"[resource_path] {relative_path} resolved to {full_path}")
        return full_path
    except Exception as e:
        print(f"[resource_path ERROR] {e}")
        return relative_path

def load_senders():
    env_path = resource_path(".env")
    log(f"[ENV] Trying to load .env from: {env_path}")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        senders_raw = os.getenv('TARGET_SENDERS', '')
        log(f"[ENV] Loaded TARGET_SENDERS raw: {senders_raw}")
        return [s.strip().lower() for s in senders_raw.split(',') if s.strip()]
    else:
        log("[ENV] .env file not found. No senders loaded.")
    return []

TARGET_SENDERS = load_senders()

def show_windows_toast(title: str, msg: str, duration_sec=5):
    try:
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);
        $textNodes = $template.GetElementsByTagName("text");
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null;
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{msg}")) > $null;
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template);
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("GmailWatcher");
        $notifier.Show($toast);
        Start-Sleep -Seconds {duration_sec};
        '''

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo
        )
    except Exception as e:
        log(f"[Toast Notification ERROR] {e}")

def open_browser_chrome(url):
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

        if os.path.exists(chrome_path):
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
            webbrowser.get('chrome').open(url)
            log(f"[AUTH] Opened URL in Chrome: {url}")
        else:
            log("[AUTH WARNING] Chrome not found. Falling back to system default browser.")
            webbrowser.open(url)
    except Exception as e:
        log(f"[Browser Open ERROR] {e}")

def authenticate_gmail():
    try:
        creds = None
        token_path = os.path.join(os.path.dirname(sys.executable), "token.json")
        credentials_path = resource_path("credentials.json")
        log(f"[AUTH] Checking for token.json at: {token_path}")
        log(f"[AUTH] Checking for credentials.json at: {credentials_path}")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            log("[AUTH] Loaded token.json successfully.")

        if not creds or not creds.valid:
            log("[AUTH] No valid token found. Starting manual browser OAuth flow...")

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')

            open_browser_chrome(auth_url)
            show_windows_toast("🔐 Gmail Login Required", "Check Chrome to complete login", duration_sec=10)

            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
            log("[AUTH] New token.json saved.")

        return build('gmail', 'v1', credentials=creds)

    except Exception as e:
        log(f"[AUTH ERROR] {e}")
        raise

def check_new_emails(service, seen_ids):
    try:
        result = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
        messages = result.get('messages', [])
        log(f"[CHECK] Found {len(messages)} unread messages.")

        for msg in messages:
            msg_id = msg['id']
            if msg_id in seen_ids:
                continue
            seen_ids.add(msg_id)

            message = service.users().messages().get(userId='me', id=msg_id, format='metadata',
                                                     metadataHeaders=['From', 'Subject']).execute()
            headers = message['payload']['headers']

            sender = subject = ''
            for h in headers:
                if h['name'] == 'From':
                    sender = h['value']
                elif h['name'] == 'Subject':
                    subject = h['value']

            sender_email = parseaddr(sender)[1].lower()
            log(f"[EMAIL] From: {sender_email}, Subject: {subject}")

            if sender_email in TARGET_SENDERS:
                log(f"[MATCH] Match found for: {sender_email}")
                try:
                    show_windows_toast(f"📬 New Mail from {sender_email}", subject or "(No Subject)", duration_sec=10)
                    log("[NOTIFY] Toast shown successfully.")
                    time.sleep(1)
                except Exception as e:
                    log(f"[NOTIFY ERROR] {e}")

    except Exception as e:
        log(f"[CHECK ERROR] {e}")

def main():
    log("🚀 Script started.")
    log(f"[INFO] TARGET_SENDERS loaded: {TARGET_SENDERS}")
    try:
        log("[INFO] Starting Gmail authentication...")
        service = authenticate_gmail()
        log("[INFO] Gmail authenticated successfully.")
    except Exception as e:
        log(f"[CRITICAL] Gmail authentication failed: {e}")
        return

    seen_ids = set()

    try:
        while True:
            check_new_emails(service, seen_ids)
            time.sleep(30)  # increased interval to avoid quota issues
    except KeyboardInterrupt:
        log("[INFO] Script stopped by user (KeyboardInterrupt).")

if __name__ == '__main__':
    main()
