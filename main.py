from fastapi import FastAPI, HTTPException
import feedparser
import os
import requests

app = FastAPI()

# 📌 Liste der RSS-Feeds, die abgefragt werden
RSS_FEEDS = [
    "https://www.tagesschau.de/xml/rss2",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
]

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
            "/send": "Sendet News an den Telegram-Bot"
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
