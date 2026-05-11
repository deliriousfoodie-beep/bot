import asyncio
import discord
import os
from playwright.async_api import async_playwright

# CONFIG
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def capture_fear_greed():
    async with async_playwright() as p:
        # Launching headless for GitHub Actions
        browser = await p.chromium.launch(headless=True)
        # Use a high device scale factor for a crisp image
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 1200},
            device_scale_factor=2
        )
        page = await context.new_page()
        
        print("🚀 Opening FearGreedMeter.com...")
        url = "https://feargreedmeter.com/fear-and-greed-index"
        
        try:
            # 1. Navigate to the new URL
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 2. Clean up any ads or banners that might block the view
            # This site is cleaner, but we'll still scrub common junk
            await page.add_style_tag(content="""
                ins, .ad-container, #google_ads_iframe, .banner-ad { 
                    display: none !important; 
                }
                /* Ensure background is clean */
                html, body { background-color: white !important; }
            """)
            
            # 3. Short wait for the specific meter animation to finish
            print("⏳ Finalizing render...")
            await asyncio.sleep(7) 
            
            path = "fear_greed.png"
            
            # 4. Target the specific meter section
            # On this site, the meter is usually inside a container with a class like 'gauge-container' 
            # but we will use a clip to get a clean, wide shot of the top section.
            # Start at y=100 to skip any top-nav bars.
            await page.screenshot(path=path, clip={'x': 0, 'y': 100, 'width': 1280, 'height': 850})
            
            print("✅ Captured FearGreedMeter successfully.")
            await browser.close()
            return path
            
        except Exception as e:
            print(f"❌ Failed to capture: {e}")
            if 'browser' in locals():
                await browser.close()
            return None

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        image_path = await capture_fear_greed()
        if image_path:
            with open(image_path, "rb") as f:
                # Updated link for the Discord title
                title = "📈 [**Fear & Greed Meter**](https://feargreedmeter.com/fear-and-greed-index)"
                await channel.send(title, file=discord.File(f), suppress_embeds=True)
            os.remove(image_path)
        else:
            await channel.send("❌ Failed to capture the Fear & Greed Meter.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
