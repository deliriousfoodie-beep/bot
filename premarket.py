import discord
import os
import asyncio

# -----------------------------
# CONFIG
# -----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# -----------------------------
# REPORT
# -----------------------------
async def generate_report():
    try:
        report = []

        report.append("📊 **Premarket Dashboard**")

        report.append("\n🔗 Market Links")

        report.append(
            "[Premarket Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gainers/)"
            "[Premarket Most Active](https://www.tradingview.com/markets/stocks-usa/market-movers-active-pre-market-stocks/)"
            "[Premarket Gap](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gappers/)"
        )

        return "\n".join(report)

    except Exception as e:
        return f"❌ Report error: {e}"

# -----------------------------
# DISCORD BOT
# -----------------------------
async def main():
    report = await generate_report()

    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        try:
            channel = await client.fetch_channel(CHANNEL_ID)
            await channel.send(report, suppress_embeds=True)
            print("Premarket report sent")
        except Exception as e:
            print(f"Discord error: {e}")

        await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"Login error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
