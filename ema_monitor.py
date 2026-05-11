import yfinance as yf
import pandas as pd
import smtplib
from email.message import EmailMessage
import os

# --- CONFIG ---
TICKER = "AIRS"
EMA_PERIODS = [10, 20, 50, 200]

# These now pull from GitHub Secrets for security
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS") 
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def check_ema_cross():
    # We fetch 2y to ensure the 200 EMA is calculated correctly from the start
    data = yf.download(TICKER, period="2y", interval="1d")
    if data.empty:
        print("❌ No data found.")
        return

    # current_price is today's latest close/price
    current_price = data['Close'].iloc[-1]
    
    alerts = []
    
    for period in EMA_PERIODS:
        # Calculate EMA using the standard 'ewm' method
        ema = data['Close'].ewm(span=period, adjust=False).mean()
        latest_ema = ema.iloc[-1]
        previous_ema = ema.iloc[-2]
        previous_price = data['Close'].iloc[-2]

        # LOGIC: Price was ABOVE yesterday, now it is BELOW today
        if previous_price > previous_ema and current_price < latest_ema:
            alerts.append(f"⚠️ {TICKER} broke BELOW the {period} EMA!\nPrice: ${current_price:.2f} | EMA: ${latest_ema:.2f}")

    if alerts:
        send_email("\n\n".join(alerts))
    else:
        print("✅ No new EMA breakdowns detected.")

def send_email(content):
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = f"🚨 AIRS Technical Alert: EMA Breakdown"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("📧 Alert email sent to your inbox.")

if __name__ == "__main__":
    check_ema_cross()
