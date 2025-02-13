from fastapi import FastAPI, HTTPException
import feedparser
import os
import json
import requests

app = FastAPI()

# 📌 JSON-Datei mit RSS-Feeds
SOURCES_FILE = "sources.json"

def load_sources():
    """🔄 Lädt die RSS-Quellen aus der sources.json-Datei"""
    if not os.path.exists(SOURCES_FILE):
        return []
    
    with open(SOURCES_FILE, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
            return [feed["url"] for feed in data.get("feeds", []) if feed["enabled"]]
        except json.JSONDecodeError:
            return []  # Falls die Datei fehlerhaft ist

# 📥 Lade alle RSS-Feeds aus der Datei
RSS_FEEDS = load_sources()

# 🔑 Telegram API Konfiguration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


@app.get("/")
def home():
    """🏠 Startseite der API"""
    return {
        "message": "🚀 FastAPI läuft auf Render!",
        "endpoints": {
            "/rss": "Holt die neuesten RSS-News",
            "/send": "Sendet News an den Telegram-Bot",
            "/feeds": "Listet gespeicherte RSS-Feeds auf",
            "/add_feed?name=XYZ&url=XYZ&category=XYZ": "Fügt eine neue Quelle hinzu",
            "/remove_feed?name=XYZ": "Löscht eine Quelle"
        }
    }


def fetch_rss_news():
    """🔍 Holt die neuesten Nachrichten aus RSS-Feeds"""
    news_list = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if "entries" in feed:
                for entry in feed.entries[:3]:  # Nur die 3 neuesten Artikel pro Feed
                    news_list.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.summary
                    })
        except Exception as e:
            print(f"❌ Fehler beim Abrufen von {feed_url}: {e}")
    return news_list


@app.get("/rss")
def get_news():
    """📰 Gibt die neuesten Nachrichten als JSON zurück"""
    news = fetch_rss_news()
    if not news:
        raise HTTPException(status_code=500, detail="Keine Nachrichten gefunden.")
    return {"news": news}


def send_telegram_message(news):
    """📩 Sendet die News als Nachricht an Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return "❌ Fehlende Telegram-Umgebungsvariablen!"

    for item in news:
        message = f"📰 *{item['title']}*\n🔗 {item['link']}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            print(f"❌ Fehler beim Senden der Nachricht: {response.text}")


@app.get("/send")
def send_news_to_telegram():
    """📲 Sendet die neuesten Nachrichten an den Telegram-Bot"""
    news = fetch_rss_news()
    if not news:
        raise HTTPException(status_code=500, detail="Keine Nachrichten zum Senden gefunden.")
    
    send_telegram_message(news)
    return {"message": "📤 News an Telegram gesendet!"}


# 🔧 RSS-Feed Verwaltung API
@app.get("/feeds")
def list_feeds():
    """📂 Listet die gespeicherten RSS-Feeds auf"""
    with open(SOURCES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data.get("feeds", [])

@app.post("/add_feed")
def add_feed(name: str, url: str, category: str):
    """➕ Fügt einen neuen RSS-Feed hinzu"""
    with open(SOURCES_FILE, "r+", encoding="utf-8") as file:
        data = json.load(file)
        feeds = data.get("feeds", [])

        # Prüfen, ob die URL bereits existiert
        if any(feed["url"] == url for feed in feeds):
            raise HTTPException(status_code=400, detail="Feed existiert bereits!")

        # Feed hinzufügen
        new_feed = {"name": name, "url": url, "category": category, "enabled": True}
        feeds.append(new_feed)
        data["feeds"] = feeds

        # Datei aktualisieren
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

    return {"message": f"✅ RSS-Feed '{name}' wurde hinzugefügt!"}

@app.delete("/remove_feed")
def remove_feed(name: str):
    """❌ Entfernt einen RSS-Feed"""
    with open(SOURCES_FILE, "r+", encoding="utf-8") as file:
        data = json.load(file)
        feeds = data.get("feeds", [])

        # Filtere den Feed raus
        updated_feeds = [feed for feed in feeds if feed["name"] != name]

        if len(updated_feeds) == len(feeds):
            raise HTTPException(status_code=404, detail="Feed nicht gefunden!")

        data["feeds"] = updated_feeds

        # Datei aktualisieren
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

    return {"message": f"🗑️ RSS-Feed '{name}' wurde entfernt!"}
