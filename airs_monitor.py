import yfinance as yf
import pandas as pd
import discord
import os
import asyncio

# --- CONFIG ---
TICKER = "AIRS"
EMA_PERIODS = [10, 20, 50, 200]
TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("MY_DISCORD_USER_ID"))

async def check_for_live_cross():
    print(f"📡 Monitoring {TICKER} for live EMA crosses...")
    
    # 1. Fetch Daily Data for the EMA levels (need 2y for accurate 200 EMA)
    daily_data = yf.download(TICKER, period="2y", interval="1d", progress=False)
    # 2. Fetch Latest Intraday Price
    intraday = yf.download(TICKER, period="1d", interval="1m", progress=False)
    
    if daily_data.empty or intraday.empty or len(intraday) < 2:
        return None

    # Handle MultiIndex
    if isinstance(daily_data.columns, pd.MultiIndex):
        daily_close = daily_data['Close'][TICKER]
        intra_close = intraday['Close'][TICKER]
    else:
        daily_close = daily_data['Close']
        intra_close = intraday['Close']

    current_price = float(intra_close.iloc[-1])
    last_minute_price = float(intra_close.iloc[-2])
    
    alerts = []
    for period in EMA_PERIODS:
        ema = daily_close.ewm(span=period, adjust=False).mean()
        latest_ema = float(ema.iloc[-1])

        # CROSS BELOW: Was above 1m ago, now below
        if last_minute_price >= latest_ema and current_price < latest_ema:
            alerts.append(f"🔴 **LIVE CROSS BELOW**: {TICKER} just dropped under {period} EMA (${latest_ema:.2f})!")
        
        # CROSS ABOVE: Was below 1m ago, now above
        if last_minute_price <= latest_ema and current_price > latest_ema:
            alerts.append(f"🟢 **LIVE CROSS ABOVE**: {TICKER} just broke over {period} EMA (${latest_ema:.2f})!")

    if alerts:
        return f"🚨 **AIRS Live Alert**\nCurrent Price: ${current_price:.2f}\n" + "\n".join(alerts)
    return None

async def main():
    message = await check_for_live_cross()
    if not message:
        print("✅ No cross detected. Standing by.")
        return

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        user = await client.fetch_user(USER_ID)
        await user.send(message)
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
