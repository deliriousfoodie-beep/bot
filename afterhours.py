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
# GET SPY AFTER-HOURS MOVE
# -----------------------------
def get_afterhours_move():
    try:
        spy = yf.download("SPY", period="2d", interval="1d", progress=False)

        if spy.empty or len(spy) < 2:
            return None

        close = float(spy["Close"].iloc[-1])
        prev_close = float(spy["Close"].iloc[-2])

        move = ((close - prev_close) / prev_close) * 100
        return move

    except Exception:
        return None

# -----------------------------
# REGIME CLASSIFICATION
# -----------------------------
def get_regime(move):
    try:
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)

        if vix.empty:
            return "Mixed"

        vix_val = float(vix["Close"].iloc[-1])

        score = 0

        # After-hours move influence
        if move is not None:
            if move > 0.5:
                score += 1
            elif move < -0.5:
                score -= 1

        # Volatility influence
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
# FADE RISK DETECTOR
# -----------------------------
def get_fade_risk(move, regime):
    if move is None:
        return "⚠️ No signal"

    if abs(move) > 1.0 and regime == "Neutral":
        return "⚠️ High Fade Risk (likely reversal at open)"

    if abs(move) < 0.2:
        return "🟡 Low conviction move"

    if move > 0.5 and regime == "Risk-On":
        return "🟢 Bullish continuation likely"

    if move < -0.5 and regime == "Risk-Off":
        return "🔴 Bearish continuation likely"

    return "🟡 Mixed conditions"

# -----------------------------
# REPORT
# -----------------------------
async def generate_report():
    try:
        move = get_afterhours_move()
        regime = get_regime(move)
        fade = get_fade_risk(move, regime)

        report = []

        report.append("🌙 **After-Hours Regime Engine**")

        # MOVE
        if move is not None:
            emoji = "🟢" if move > 0 else "🔴"
            report.append(f"\n{emoji} SPY After-Hours Move: {move:+.2f}%")
        else:
            report.append("\n⚠️ SPY After-Hours Move: Unavailable")

        # REGIME
        report.append(f"🧭 Market Regime: **{regime}**")

        # FADE RISK / BIAS
        report.append(f"⚠️ Signal: **{fade}**")

        # LINKS
        report.append("\n🔗 Market Links")
        report.append("[After-Hours Gainers](https://www.tradingview.com/markets/stocks-usa/market-movers-after-hours-gainers/)")
        report.append("[After-Hours Losers](https://www.tradingview.com/markets/stocks-usa/market-movers-after-hours-losers/)")
        report.append("[Earnings Calendar](https://finance.yahoo.com/calendar/earnings/)")

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
            print("After-hours report sent")
        except Exception as e:
            print(f"Discord error: {e}")

        await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"Login error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
