import yfinance as yf
import discord
import os
import asyncio

# -----------------------------
# CONFIG
# -----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# -----------------------------
# GET SPY GAP %
# -----------------------------
def get_spy_gap():
    try:
        spy = yf.download("SPY", period="2d", interval="1d", progress=False)

        if spy.empty or len(spy) < 2:
            return None

        prev_close = float(spy["Close"].iloc[-2])
        current = float(spy["Close"].iloc[-1])

        gap = ((current - prev_close) / prev_close) * 100
        return gap

    except Exception:
        return None

# -----------------------------
# MARKET REGIME
# -----------------------------
def get_regime(gap):
    try:
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)

        if vix.empty:
            return "Mixed"

        vix_val = float(vix["Close"].iloc[-1])

        score = 0

        # SPY gap influence
        if gap is not None:
            if gap > 0.3:
                score += 1
            elif gap < -0.3:
                score -= 1

        # VIX influence
        if vix_val < 18:
            score += 1
        elif vix_val > 25:
            score -= 1

        if score >= 2:
            return "Risk-On"
        elif score == 1:
            return "Neutral"
        elif score == 0:
            return "Mixed"
        else:
            return "Risk-Off"

    except Exception:
        return "Mixed"

# -----------------------------
# TRADE BIAS
# -----------------------------
def get_bias(gap, regime):
    if gap is None:
        return "⚠️ No signal"

    if regime == "Risk-On" and gap > 0:
        return "🟢 Bullish Bias"
    elif regime == "Risk-Off" and gap < 0:
        return "🔴 Bearish Bias"
    elif abs(gap) < 0.2:
        return "🟡 Neutral / Chop"
    else:
        return "🟡 Mixed Conditions"

# -----------------------------
# REPORT
# -----------------------------
async def generate_report():
    try:
        gap = get_spy_gap()
        regime = get_regime(gap)
        bias = get_bias(gap, regime)

        report = []

        report.append("📊 **Premarket Signal Engine**")

        # SPY GAP
        if gap is not None:
            emoji = "🟢" if gap > 0 else "🔴"
            report.append(f"\n{emoji} SPY Gap: {gap:+.2f}%")
        else:
            report.append("\n⚠️ SPY Gap: Unavailable")

        # REGIME
        report.append(f"🧭 Market Regime: **{regime}**")

        # SIGNAL
        report.append(f"⚠️ Bias: **{bias}**")

        # LINKS
        report.append("\n🔗 Market Links")

        report.append("[Premarket Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gainers/)")
        report.append("[Premarket Most Active](https://www.tradingview.com/markets/stocks-usa/market-movers-active-pre-market-stocks/)")
        report.append("[Premarket Gappers](https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gappers/)")

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
            print("Premarket signal sent")
        except Exception as e:
            print(f"Discord error: {e}")

        await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"Login error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
