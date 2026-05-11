import asyncio
import discord
import os
from playwright.async_api import async_playwright

# CONFIG
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def get_today_earnings():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        url = "https://finance.yahoo.com/calendar/earnings?offset=0&size=100"
        print(f"Opening {url}...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for the table to appear
            await page.wait_for_selector("table", timeout=30000)
            
            # Target the table rows
            rows = await page.query_selector_all("tbody tr")
            
            all_messages = []
            current_chunk = ["📅 [**TODAY'S EARNINGS CALENDAR**](https://finance.yahoo.com/calendar/earnings)", ""]
            current_chunk.append("**TICKER | COMPANY NAME**")
            current_chunk.append("------------------------------")
            
            count = 0
            for row in rows:
                # Get all cells in the row
                cells = await row.query_selector_all("td")
                if len(cells) < 2:
                    continue
                
                # Yahoo Finance Table structure:
                # Cell 0: Ticker
                # Cell 1: Company Name
                ticker = await cells[0].inner_text()
                company = await cells[1].inner_text()
                
                # Clean up text
                ticker = ticker.strip()
                company = company.strip()
                
                # Format the link
                ticker_link = f"[{ticker}](https://www.tradingview.com/chart/?symbol={ticker})"
                line = f"{ticker_link} | {company}"
                
                # Check Discord character limit (2000 total, we use 1800 for safety)
                current_length = len("\n".join(current_chunk))
                if current_length + len(line) > 1800:
                    all_messages.append("\n".join(current_chunk))
                    current_chunk = [line]
                else:
                    current_chunk.append(line)
                
                count += 1
                if count >= 100: break

            if current_chunk:
                all_messages.append("\n".join(current_chunk))

            await browser.close()
            return all_messages if count > 0 else ["⚠️ No earnings found for today."]
            
        except Exception as e:
            await browser.close()
            return [f"❌ Scraper Error: {str(e)}"]

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        reports = await get_today_earnings()
        for msg in reports:
            await channel.send(msg, suppress_embeds=True)
            await asyncio.sleep(1.5) # Prevents message re-ordering
        print("Success.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)