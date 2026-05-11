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
                user_data_dir, headless=True, **device_config
            )
            page = context.pages[0]
            await page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")
            
            url = "https://www.tradingview.com/markets/stocks-usa/market-movers-unusual-volume/"
            await page.goto(url, wait_until="load")
            
            # Wait for rows and scroll more to ensure 100 rows are loaded in the DOM
            await page.wait_for_selector("tbody tr", timeout=30000)
            await page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(5) 

            rows = await page.query_selector_all("tbody tr")

            all_messages = []
            # Starting Header
            current_chunk = ["🚀 [**Unusual Volume**](https://www.tradingview.com/markets/stocks-usa/market-movers-unusual-volume/)", ""]
            current_chunk.append("**TICKER | PRICE | GAINS**")
            current_chunk.append("------------------------------")

            count = 0
            for row in rows:
                if count >= 100: break # Increased limit to 100
                
                row_text = await row.inner_text()
                ticker_match = re.search(r'^[A-Z]+', row_text.strip())
                if not ticker_match: continue
                ticker = ticker_match.group()

                chg_match = re.search(r'([+-−][0-9.]+\%)', row_text)
                change = chg_match.group(1) if chg_match else "N/A"

                price_match = re.search(r'([0-9.]+) USD', row_text)
                price = f"${price_match.group(1)}" if price_match else "N/A"

                if ticker and change != "N/A":
                    ticker_link = f"[{ticker}](https://www.tradingview.com/chart/?symbol={ticker})"
                    line = f"{ticker_link} | {price} | {change}"
                    
                    # Calculate current length including newlines
                    current_length = len("\n".join(current_chunk))
                    
                    # If adding this line hits ~1800 chars, ship the current chunk
                    if current_length + len(line) > 1800:
                        all_messages.append("\n".join(current_chunk))
                        # Start new chunk without the header (to save space)
                        current_chunk = [line] 
                    else:
                        current_chunk.append(line)
                    
                    count += 1

            # Add the final leftover chunk
            if current_chunk:
                all_messages.append("\n".join(current_chunk))

            await context.close()
            return all_messages
            
        except Exception as e:
            return [f"❌ Error: {str(e)}"]

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        reports = await get_tradingview_gainers()
        for i, msg in enumerate(reports):
            # Suppress embeds and send chunks
            await channel.send(msg, suppress_embeds=True)
            # Short sleep to prevent Discord from rate-limiting or re-ordering
            await asyncio.sleep(1.5) 
        print(f"Success: Sent {len(reports)} message(s).")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
