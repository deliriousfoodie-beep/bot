import asyncio
import discord
import os
from playwright.async_api import async_playwright

# CONFIG
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def capture_heatmap():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        # Use a standard 1080p Desktop view
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("🚀 Opening TradingView Heatmap...")
        url = "https://www.tradingview.com/heatmap/stock/#%7B%22index%22%3A%22S%26P500%22%7D"
        
        try:
            # 1. Just wait for the URL to load basically
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 2. Wait 15 seconds. No selectors, no locators. 
            # Just pure waiting for the graphics to finish drawing.
            print("⏳ Waiting 15s for the map to render colors...")
            await asyncio.sleep(15) 
            
            # 3. Snapshot the whole viewport
            path = "heatmap.png"
            await page.screenshot(path=path)
            
            print("✅ Screenshot captured successfully!")
            await browser.close()
            return path
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            await browser.close()
            return None

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        image_path = await capture_heatmap()
        if image_path:
            with open(image_path, "rb") as f:
                await channel.send("📊 **Today's S&P 500 Heatmap:**", file=discord.File(f))
            os.remove(image_path)
        else:
            await channel.send("❌ Heatmap capture timed out again. The site might be blocking headless browsers.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)