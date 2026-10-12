import os
import time
import cloudscraper
from bs4 import BeautifulSoup

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
            print(f"[{name}] Blocked or Status Code: {response.status_code}")
            return False

        text = response.text.lower()

        # Anti-bot / Cloudflare check
        if "captcha" in text or "access denied" in text or "security check" in text:
            print(f"[{name}] Hit anti-bot page, skipping.")
            return False

        # JioGames ke liye special handling (agar page par 'sold out' ya 'out of stock' hidden ya visible ho)
        if name == "JioGames":
            if "out of stock" in text or "sold out" in text or "currently unavailable" in text:
                print(f"[JioGames] Verified: Actually Out of Stock.")
                return False
            # Agar 'pay ₹' dikh raha hai par saath me stock nahi hai, toh ye check lagayein
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            if "pay ₹" in page_text and not ("out of stock" in page_text or "unavailable" in page_text):
                # Additional safety: check if actual vouchers are disabled/sold out
                print(f"[JioGames] 🔥 Real Stock Likely Available!")
                return True
            return False

        # Baaki sites ke liye standard logic
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()

        positive_keywords = ["add to cart", "buy now", "proceed to buy", "pay ₹"]
        negative_keywords = ["out of stock", "currently unavailable", "sold out", "coming soon", "temporarily unavailable"]

        has_positive = any(keyword in page_text for keyword in positive_keywords)
        has_negative = any(keyword in page_text for keyword in negative_keywords)

        if has_positive and not has_negative:
            print(f"[{name}] 🔥 Real Stock Detected!")
            return True
        else:
            print(f"[{name}] Out of stock.")
            return False

    except Exception as e:
        print(f"[{name}] Error checking page: {e}")
        return False

def main():
    print("🚀 Advanced PSN Stock Checker Active...")
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
    
