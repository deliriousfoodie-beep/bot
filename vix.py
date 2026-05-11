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
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1800})
        page = await context.new_page()
        
        print("🚀 Opening CNN Fear & Greed Index...")
        url = "https://www.cnn.com/markets/fear-and-greed"
        
        try:
            # 1. Wait for the page to be quiet
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 2. THE NUCLEAR OPTION (Restored)
            # This is the exact CSS block that cleared the banner for you before.
            await page.add_style_tag(content="""
                #onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter { 
                    display: none !important; 
                }
                /* Hide everything that might overlap the content */
                div[role="dialog"], div[class*="overlay"], div[class*="modal"] {
                    display: none !important;
                }
                /* Force brightness and visibility */
                html, body { 
                    filter: none !important; 
                    background-color: white !important; 
                    overflow: visible !important;
                }
            """)
            
            # 3. Scroll to trigger animations and reach the Momentum chart
            # Scrolling 450px as requested earlier for the 15% drop
            await page.evaluate("window.scrollBy(0, 450)")
            
            print("⏳ Rendering charts (sequential mode)...")
            # Extra sleep to ensure the "White Box" doesn't happen during high workflow load
            await asyncio.sleep(12) 
            
            path = "fear_greed.png"
            
            # 4. Use the coordinate-based clip to capture both Dial and Momentum
            # This avoids the banner even if a tiny piece of it is still floating elsewhere
            await page.screenshot(path=path, clip={'x': 0, 'y': 250, 'width': 1280, 'height': 1300})
            
            print("✅ Fear & Greed captured (Banner Scrubbed).")
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
                title = "📈 [**Fear & Greed Index**](https://www.cnn.com/markets/fear-and-greed)"
                await channel.send(title, file=discord.File(f), suppress_embeds=True)
            os.remove(image_path)
        else:
            await channel.send("❌ Failed to capture the Fear & Greed Index.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
