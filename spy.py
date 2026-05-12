import yfinance as yf
import pandas as pd
import discord
import os
import asyncio
import requests
import re
from bs4 import BeautifulSoup

# -----------------------------
# CONFIG
# -----------------------------
TICKER = "SPY"
EMA_PERIODS = [10, 20, 50, 200]

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# -----------------------------
# SECTORS (ticker → name)
# -----------------------------
SECTORS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "XLU": "Utilities"
}

# -----------------------------
# FEAR & GREED
# -----------------------------
def get_fear_greed():
    try:
        url = "https://feargreedmeter.com/"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ", strip=True)
        matches = re.findall(r'\b([1-9]?\d|100)\b', text)

        value = next((int(m) for m in matches if 0 <= int(m) <= 100), None)

        if value is None:
            return "❌ Fear & Greed unavailable"

        if value <= 24:
            return f"🔴 Fear & Greed: {value} (Extreme Fear)"
        elif value <= 44:
            return f"🟠 Fear & Greed: {value} (Fear)"
        elif value <= 54:
            return f"🟡 Fear & Greed: {value} (Neutral)"
        elif value <= 74:
            return f"🟢 Fear & Greed: {value} (Greed)"
        else:
            return f"🚀 Fear & Greed: {value} (Extreme Greed)"

    except Exception as e:
        return f"❌ Fear & Greed error: {e}"

# -----------------------------
# MARKET REGIME ENGINE (SAFE)
# -----------------------------
def get_market_regime():
    try:
        spy_df = yf.download("SPY", period="6mo", interval="1d", progress=False)
        vix_df = yf.download("^VIX", period="1mo", interval="1d", progress=False)
        dxy_df = yf.download("DX-Y.NYB", period="1mo", interval="1d", progress=False)

        if spy_df.empty or vix_df.empty or dxy_df.empty:
            return "🟡 Market Regime: DATA UNAVAILABLE"

        spy = spy_df["Close"]
        vix = vix_df["Close"]
        dxy = dxy_df["Close"]

        price = float(spy.iloc[-1])
        trend = float(spy.ewm(span=50).mean().iloc[-1])

        vix_val = float(vix.iloc[-1])
        dxy_val = float(dxy.iloc[-1])

        score = 0

        if price > trend:
            score += 1
        else:
            score -= 1

        if vix_val < 18:
            score += 1
        elif vix_val > 25:
            score -= 1

        if dxy_val < float(dxy.rolling(20).mean().iloc[-1]):
            score += 1
        else:
            score -= 1

        if score >= 2:
            return "🟢 Market Regime: RISK-ON"
        elif score == 1:
            return "🟡 Market Regime: NEUTRAL"
        elif score == 0:
            return "🟠 Market Regime: MIXED / ROTATION"
        else:
            return "🔴 Market Regime: RISK-OFF"

    except Exception as e:
        return f"❌ Market Regime error: {e}"

# -----------------------------
# SECTOR LEADERS (SAFE)
# -----------------------------
def get_sector_leaders():
    try:
        results = []

        for ticker, name in SECTORS.items():
            df = yf.download(ticker, period="6d", interval="1d", progress=False)

            if df.empty or "Close" not in df:
                continue

            close = df["Close"]

            if len(close) < 2:
                continue

            change = ((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100
            results.append((name, change))

        if not results:
            return "❌ Sector data unavailable"

        results.sort(key=lambda x: x[1], reverse=True)

        lines = ["\n🏆 **Sector Leaders (5D)**"]

        for i, (name, chg) in enumerate(results, 1):
            emoji = "🟢" if chg > 0 else "🔴"
            lines.append(f"{i}. {emoji} {name}: {chg:+.2f}%")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Sector error: {e}"

# -----------------------------
# MAIN REPORT
# -----------------------------
async def generate_report():
    data = yf.download(TICKER, period="2y", interval="1d", progress=False)

    if data.empty:
        return "❌ SPY data unavailable"

    close = data["Close"]
    price = float(close.iloc[-1])

    report = [
        f"📊 **{TICKER} Market Dashboard** (${price:.2f})"
    ]

    for p in EMA_PERIODS:
        ema = close.ewm(span=p).mean().iloc[-1]
        status = "🟢 ABOVE" if price > ema else "🔴 BELOW"
        report.append(f"{status} {p} EMA: ${ema:.2f}")

    report.append("")
    report.append(get_fear_greed())
    report.append(get_market_regime())
    report.append(get_sector_leaders())

    report.append("\n🔗 **Market Links**")
    report.append("[Top Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-gainers/)")
    report.append("[Premarket Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gainers/)")
    report.append("[Unusual Volume](https://www.tradingview.com/markets/stocks-usa/market-movers-unusual-volume/)")

    return "\n".join(report)

# -----------------------------
# DISCORD BOT
# -----------------------------
async def main():
    report = await generate_report()

    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        channel = client.get_channel(CHANNEL_ID)

        if channel:
            await channel.send(report, suppress_embeds=True)

        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
