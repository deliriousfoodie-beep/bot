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
        # We increase the viewport height to 1800 to fit both charts
        context = await browser.new_context(viewport={'width': 1280, 'height': 1800})
        page = await context.new_page()
        
        print("🚀 Opening CNN Fear & Greed Index & Market Momentum...")
        url = "https://www.cnn.com/markets/fear-and-greed"
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # THE NUCLEAR OPTION (Hiding the banner and the dark contrast filter)
            await page.add_style_tag(content="""
                #onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter { 
                    display: none !important; 
                }
                div[role="dialog"], div[class*="overlay"], div[class*="modal"] {
                    display: none !important;
                }
                /* Ensure the background stays bright even if the overlay is hidden */
                html, body { 
                    filter: none !important; 
                    background-color: white !important; 
                }
            """)
            
            await page.evaluate("document.body.style.overflow = 'visible';")

            # 🚀 SCROLL ADJUSTMENT:
            # We scroll down about 450 pixels to center the momentum chart
            await page.evaluate("window.scrollBy(0, 450)")
            
            print("⏳ Rendering dial and momentum charts...")
            await asyncio.sleep(10) 
            
            path = "fear_greed.png"
            
            # Instead of just the fng-container (which is often just the dial),
            # we capture a specific section of the page that contains both.
            # 1400 height captures the Dial + Momentum + Junk removal.
            await page.screenshot(path=path, clip={'x': 0, 'y': 250, 'width': 1280, 'height': 1400})
            
            print("✅ Captured Dial and Market Momentum.")
            await browser.close()
            return path
            
        except Exception as e:
            print(f"❌ Failed to capture: {e}")
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
            await channel.send("❌ Failed to capture the charts.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)