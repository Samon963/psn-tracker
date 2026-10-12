import os
import time
import cloudscraper
from bs4 import BeautifulSoup

# Telegram Config (GitHub Secrets से aayenge)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TARGET_URLS = {
    "GyFTR": "https://www.gyftr.com/sony-playstation",
    "JioGames": "https://store.jiogames.com/products/?brand=playstation",
    "Amazon": "https://www.amazon.in/dp/B08L5WH137", 
    "Flipkart": "https://www.flipkart.com/search?q=playstation+gift+card"
}

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        scraper.post(url, json=payload)
    except Exception as e:
        print(f"Telegram alert error: {e}")

def check_site(name, url):
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            print(f"[{name}] Status Code: {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()

        out_of_stock_phrases = [
            "out of stock", "currently unavailable", "sold out", 
            "coming soon", "temporarily unavailable", "item not available"
        ]

        is_out = any(phrase in text for phrase in out_of_stock_phrases)

        if is_out:
            print(f"[{name}] Currently Out of Stock.")
            return False
        else:
            print(f"[{name}] 🔥 Stock Detected / Available!")
            return True

    except Exception as e:
        print(f"[{name}] Error checking page: {e}")
        return False

def main():
    print("🚀 PSN Stock Checker Active...")
    alerts = []

    for platform, url in TARGET_URLS.items():
        print(f"Checking {platform}...")
        if check_site(platform, url):
            alerts.append(f"🚨 **{platform.upper()} RESTOCK ALERT!**\n👉 [Check Now]({url})")

    if alerts:
        full_message = "\n\n".join(alerts)
        send_telegram_alert(full_message)

if __name__ == "__main__":
    main()
              
