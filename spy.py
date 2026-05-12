import yfinance as yf
import pandas as pd
import discord
import os
import asyncio

# --- CONFIG ---
TICKER = "SPY"
EMA_PERIODS = [10, 20, 50, 200]
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

async def generate_spy_report():
    print(f"🔍 Fetching data for {TICKER}...")
    data = yf.download(TICKER, period="2y", interval="1d")

    if data.empty or len(data) < 200:
        return "❌ Error: Could not fetch enough data for SPY."

    # Handle MultiIndex issue
    if isinstance(data.columns, pd.MultiIndex):
        close_series = data['Close'][TICKER]
    else:
        close_series = data['Close']

    current_price = float(close_series.iloc[-1])

    report_lines = [
        f"📊 **{TICKER} EMA Status Report** (Price: ${current_price:.2f})"
    ]

    for period in EMA_PERIODS:
        ema = close_series.ewm(span=period, adjust=False).mean()
        latest_ema = float(ema.iloc[-1])

        status = "🟢 **ABOVE**" if current_price > latest_ema else "🔴 **BELOW**"
        diff = ((current_price - latest_ema) / latest_ema) * 100

        report_lines.append(
            f"{status} the **{period} EMA** (${latest_ema:.2f}) | Dist: {diff:+.2f}%"
        )

    # --- MARKET LINKS ---
    report_lines.append("\n🔗 **Market Links**")

    report_lines.append(
        "[Top Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-gainers/)"
    )

    report_lines.append(
        "[Premarket Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gainers/)"
    )

    report_lines.append(
        "[Unusual Volume](https://www.tradingview.com/markets/stocks-usa/market-movers-unusual-volume/)"
    )

    report_lines.append(
        "[Fear and Greed Index](https://www.cnn.com/markets/fear-and-greed)"
    )

    report_lines.append(
        "[Heat Map](https://www.tradingview.com/heatmap/stock/#%7B%22dataSource%22%3A%22SPX500%22%2C%22blockColor%22%3A%22change%22%2C%22blockSize%22%3A%22market_cap_basic%22%2C%22grouping%22%3A%22sector%22%7D)"
    )

    report_lines.append(
        "[Earnings Calendar](https://finance.yahoo.com/calendar/earnings?guccounter=1)"
    )

    return "\n".join(report_lines)

async def main():
    report = await generate_spy_report()

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(CHANNEL_ID)

        if channel:
            await channel.send(report)

        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
