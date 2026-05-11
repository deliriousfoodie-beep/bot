import yfinance as yf
import pandas as pd
import discord
import os
import asyncio

# --- CONFIG ---
TICKER = "AIRS"
EMA_PERIODS = [10, 20, 50, 200]
TOKEN = os.getenv("DISCORD_TOKEN")
# Replace 'YOUR_USER_ID' with your actual 18-digit ID in GitHub Secrets
USER_ID = int(os.getenv("MY_DISCORD_USER_ID")) 

async def generate_airs_report():
    print(f"🔍 Analyzing {TICKER} Trend...")
    data = yf.download(TICKER, period="2y", interval="1d")
    
    if data.empty or len(data) < 200:
        return f"❌ Error: Could not fetch enough data for {TICKER}."

    if isinstance(data.columns, pd.MultiIndex):
        close_series = data['Close'][TICKER]
    else:
        close_series = data['Close']

    current_price = float(close_series.iloc[-1])
    report_lines = [f"🛰️ **{TICKER} Private Trend Intelligence**", f"Price: **${current_price:.2f}**\n"]
    
    for period in EMA_PERIODS:
        ema = close_series.ewm(span=period, adjust=False).mean()
        latest_ema = float(ema.iloc[-1])
        status = "🟢 ABOVE" if current_price > latest_ema else "🔴 BELOW"
        diff = ((current_price - latest_ema) / latest_ema) * 100
        report_lines.append(f"{status} {period} EMA (${latest_ema:.2f}) | `{diff:+.2f}%`")

    return "\n".join(report_lines)

async def main():
    report = await generate_airs_report()
    
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}. Sending DM...")
        try:
            # This line fetches your specific user profile
            user = await client.fetch_user(USER_ID)
            # This opens the DM and sends the report
            await user.send(report)
            print("✅ DM sent successfully.")
        except Exception as e:
            print(f"❌ Failed to send DM: {e}")
        
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
