import yfinance as yf
import pandas as pd
import discord
import os
import asyncio
import requests
import re
from bs4 import BeautifulSoup

# --- CONFIG ---
TICKER = "SPY"
EMA_PERIODS = [10, 20, 50, 200]

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# -----------------------------
# FEAR & GREED SCRAPER
# -----------------------------
def get_fear_greed():
    try:
        url = "https://feargreedmeter.com/"
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text(" ", strip=True)

        # extract number 0–100
        matches = re.findall(r'\b([1-9]?\d|100)\b', text)

        value = None
        for m in matches:
            num = int(m)
            if 0 <= num <= 100:
                value = num
                break

        if value is None:
            return "❌ Fear & Greed not found"

        # sentiment mapping
        if value <= 24:
            sentiment, emoji = "Extreme Fear", "🔴"
        elif value <= 44:
            sentiment, emoji = "Fear", "🟠"
        elif value <= 54:
            sentiment, emoji = "Neutral", "🟡"
        elif value <= 74:
            sentiment, emoji = "Greed", "🟢"
        else:
            sentiment, emoji = "Extreme Greed", "🚀"

        return f"{emoji} Fear & Greed Index: **{value}** ({sentiment})"

    except Exception as e:
        return f"❌ Fear & Greed error: {e}"

# -----------------------------
# REPORT GENERATION
# -----------------------------
async def generate_spy_report():
    print(f"🔍 Fetching data for {TICKER}...")

    data = yf.download(TICKER, period="2y", interval="1d")

    if data.empty or len(data) < 200:
        return "❌ Error: Not enough SPY data."

    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"][TICKER]
    else:
        close = data["Close"]

    price = float(close.iloc[-1])

    report = [
        f"📊 **{TICKER} EMA Report** (Price: ${price:.2f})"
    ]

    for p in EMA_PERIODS:
        ema = close.ewm(span=p, adjust=False).mean()
        val = float(ema.iloc[-1])

        status = "🟢 ABOVE" if price > val else "🔴 BELOW"
        diff = ((price - val) / val) * 100

        report.append(
            f"{status} **{p} EMA** (${val:.2f}) | {diff:+.2f}%"
        )

    # -----------------------------
    # FEAR & GREED
    # -----------------------------
    report.append("")
    report.append(get_fear_greed())

    # -----------------------------
    # MARKET LINKS (CLICKABLE TEXT, NO PREVIEWS)
    # -----------------------------
    report.append("\n🔗 **Market Links**")

    report.append("[Top Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-gainers/)")
    report.append("[Premarket Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gainers/)")
    report.append("[Unusual Volume](https://www.tradingview.com/markets/stocks-usa/market-movers-unusual-volume/)")
    report.append("[Fear and Greed Index](https://www.cnn.com/markets/fear-and-greed)")
    report.append("[Heat Map](https://www.tradingview.com/heatmap/stock/#%7B%22dataSource%22%3A%22SPX500%22%2C%22blockColor%22%3A%22change%22%2C%22blockSize%22%3A%22market_cap_basic%22%2C%22grouping%22%3A%22sector%22%7D)")
    report.append("[Earnings Calendar](https://finance.yahoo.com/calendar/earnings?guccounter=1)")

    return "\n".join(report)

# -----------------------------
# DISCORD BOT
# -----------------------------
async def main():
    report = await generate_spy_report()

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ Logged in as {client.user}")

        channel = client.get_channel(CHANNEL_ID)

        if channel:
            await channel.send(report, suppress_embeds=True)
            print("✅ Sent report")
        else:
            print("❌ Channel not found")

        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
