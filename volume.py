import asyncio
import discord
import os
import re
from playwright.async_api import async_playwright

# CONFIG
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def get_tradingview_gainers():
    async with async_playwright() as p:
        device = p.devices['iPhone 13']
        device_config = {k: v for k, v in device.items() if k != 'default_browser_type'}
        user_data_dir = os.path.join(os.getcwd(), "tv_session")
        
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                **device_config,
            )
            page = context.pages[0]
            await page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")
            
            print("Fetching and cleaning TradingView data...")
            url = "https://www.tradingview.com/markets/stocks-usa/market-movers-unusual-volume/"
            await page.goto(url, wait_until="load")
            
            await page.wait_for_selector("tbody tr", timeout=30000)
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(4) 

            rows = await page.query_selector_all("tbody tr")

            bt = chr(96) * 3
            res = ["🚀 **Unusual Volume**", bt + "text"]
            res.append(f"{'TICKER':<8} | {'PRICE':<10} | {'GAINS'}")
            res.append("-" * 34)

            count = 0
            for row in rows:
                if count >= 55: break
                
                row_text = await row.inner_text()
                
                # 1. Get the Ticker (Usually the first word in the block)
                ticker_match = re.search(r'^[A-Z]+', row_text.strip())
                if not ticker_match: continue
                ticker = ticker_match.group()

                # 2. Extract the Usual Volume Percentage Change
                # Looks for + or - followed by digits and a % sign
                chg_match = re.search(r'([+-−][0-9.]+\%)', row_text)
                change = chg_match.group(1) if chg_match else "N/A"

                # 3. Extract the Price
                # Looks for digits + '.' + digits followed by 'USD'
                # Example: '0.99 USD' -> '0.99'
                price_match = re.search(r'([0-9.]+) USD', row_text)
                price = f"${price_match.group(1)}" if price_match else "N/A"

                if ticker and change != "N/A":
                    res.append(f"{ticker:<8} | {price:<10} | {change}")
                    count += 1

            res.append(bt)
            await context.close()
            return "\n".join(res) if count > 0 else "⚠️ Could not parse clean data."
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        report = await get_tradingview_gainers()
        await channel.send(report)
        print("Success.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
