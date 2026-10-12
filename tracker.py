import os
import time
import cloudscraper
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TARGET_URLS = {
    "GyFTR": "https://www.gyftr.com/sony-playstation",
    "JioGames": "https://store.jiogames.com/products/?brand=playstation",
    "Amazon": "https://amzn.in/d/0fgC6jpo", 
    "Flipkart": "https://www.flipkart.com/search?q=psn+gift+card&sid=mcd%2Czyx%2Czzo&as=on&as-show=on&as-pos=1&as-type=RECENT&as-searchtext=psn&requestId=51db7ba4-2972-4a62-8bad-4a933cad7d76&suggestionId=psn+gift+card%7CDigital+Voucher+Code&otracker=AS_QueryStore_OrganicAutoSuggest_%7BPOSITION%7D_3_na_na_na&isSearchQuery=true"
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
        response = scraper.get(url, timeout=15, allow_redirects=True)
        if response.status_code != 200:
            print(f"[{name}] Page not accessible (Status: {response.status_code})")
            return False

        text = response.text.lower()

        if "captcha" in text or "access denied" in text or "security check" in text:
            print(f"[{name}] Hit anti-bot page, skipping.")
            return False

        # GyFTR ke liye strict check taaki false alert na aaye
        if name == "GyFTR":
            if "product not found" in text or "we are sold out" in text or "sold out" in text or "out of stock" in text:
                print(f"[GyFTR] Confirmed Out of Stock via strict check.")
                return False
            # Agar actual buy option ho tabhi true maane
            if "buy now" in text or "add to cart" in text:
                print(f"[GyFTR] 🔥 Real Stock Detected!")
                return True
            return False

        # JioGames specific validation
        if name == "JioGames":
            if "out of stock" in text or "sold out" in text or "currently unavailable" in text:
                print(f"[JioGames] Out of stock confirmed.")
                return False
            if "pay ₹" in text or "select vouchers" in text:
                print(f"[JioGames] 🔥 Active Page & Stock Options Detected!")
                return True
            return False

        # Standard platforms logic (Amazon, Flipkart)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()

        positive_keywords = ["add to cart", "buy now", "proceed to buy", "pay ₹"]
        
        negative_keywords = [
            "out of stock", "currently unavailable", "sold out", 
            "coming soon", "no results found", "product not found", 
            "we are sold out", "sold-out", "notify me", 
            "item not available for purchase", "product is out of stock"
        ]

        has_positive = any(keyword in page_text for keyword in positive_keywords)
        has_negative = any(keyword in page_text for keyword in negative_keywords)

        if has_negative:
            print(f"[{name}] Confirmed Out of Stock (Negative keyword found).")
            return False

        if has_positive and not has_negative:
            print(f"[{name}] 🔥 Real Stock Detected!")
            return True
        else:
            print(f"[{name}] Out of stock or unverified.")
            return False

    except Exception as e:
        print(f"[{name}] Error checking page: {e}")
        return False

def main():
    print("🚀 Ultimate PSN Stock Checker Active...")
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
        
