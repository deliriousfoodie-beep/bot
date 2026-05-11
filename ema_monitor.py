import yfinance as yf
import pandas as pd
import smtplib
from email.message import EmailMessage
import os

# --- CONFIG ---
TICKER = "AIRS"
EMA_PERIODS = [10, 20, 50, 200]

# These pull from GitHub Secrets
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS") 
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def check_ema_cross():
    # 1. Fetch data
    print(f"🔍 Checking {TICKER}...")
    data = yf.download(TICKER, period="2y", interval="1d")
    
    # 2. SAFETY CHECK: If no data, stop here instead of crashing
    if data is None or len(data) < 200:
        print(f"📉 Not enough data for {TICKER} (Market might be closed).")
        return

    # 3. Get current price and handle potential multi-index issues
    # We use .item() to ensure we get a single float value
    current_price = float(data['Close'].iloc[-1])
    
    alerts = []
    
    for period in EMA_PERIODS:
        # Calculate EMA
        ema = data['Close'].ewm(span=period, adjust=False).mean()
        latest_ema = float(ema.iloc[-1])
        previous_ema = float(ema.iloc[-2])
        previous_price = float(data['Close'].iloc[-2])

        # LOGIC: Price was ABOVE yesterday, now it is BELOW today
        if previous_price > previous_ema and current_price < latest_ema:
            alerts.append(f"⚠️ {TICKER} broke BELOW the {period} EMA!\nPrice: ${current_price:.2f} | EMA: ${latest_ema:.2f}")

    # 4. Action
    if alerts:
        send_email("\n\n".join(alerts))
    else:
        print(f"✅ {TICKER} at ${current_price:.2f} is above your EMA levels. No alerts.")

def send_email(content):
    # If secrets are missing, don't try to send
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("❌ Error: Email credentials missing in GitHub Secrets.")
        return

    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = f"🚨 AIRS Technical Alert: EMA Breakdown"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("📧 Alert email sent to your inbox.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    check_ema_cross()
