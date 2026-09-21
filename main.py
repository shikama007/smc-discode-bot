import ccxt
import pandas as pd
import requests
import time

# ⚠️ මෙතනට ඔයාගේ Discord Webhook URL එක Paste කරන්න
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1551331530788307105/ztsU2VQsmOBSWWzXmrF32XqWwP5b3KC4-BrbJFbGA69CNIGITdbpmo-Ths1GVZL-jwgL"

def send_discord_alert(fvg_type, symbol, htf_trend, ltf, zone_bottom, zone_top, current_price):
    color = 3066993 if fvg_type == 'BULLISH' else 15158332
    
    payload = {
        "embeds": [
            {
                "title": f"🚨 HIGH-PROBABILITY SMC {fvg_type} FVG DETECTED!",
                "color": color,
                "fields": [
                    {"name": "📌 Asset", "value": f"`{symbol}`", "inline": True},
                    {"name": "📊 1H Trend", "value": f"`{htf_trend}`", "inline": True},
                    {"name": "⏱ Signal TF", "value": f"`{ltf}`", "inline": True},
                    {"name": "🎯 FVG Zone", "value": f"`${zone_bottom:.2f} - ${zone_top:.2f}`", "inline": False},
                    {"name": "💵 Current Price", "value": f"`${current_price:.2f}`", "inline": False}
                ],
                "footer": {
                    "text": "SMC Trading Bot • Confirm setup on Binance App before entry"
                }
            }
        ]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print("Discord Error:", e)

exchange = ccxt.binance({'enableRateLimit': True})

SYMBOL = 'BTC/USDT'
HTF = '1h'
LTF = '15m'

def fetch_data(symbol, timeframe, limit=50):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

def get_htf_trend(df_htf):
    ema20 = df_htf['close'].ewm(span=20, adjust=False).mean().iloc[-1]
    current_price = df_htf['close'].iloc[-1]
    return 'BULLISH' if current_price > ema20 else 'BEARISH'

def check_ltf_fvg(df_ltf, trend):
    c1_high = df_ltf.iloc[-3]['high']
    c3_low = df_ltf.iloc[-1]['low']
    c1_low = df_ltf.iloc[-3]['low']
    c3_high = df_ltf.iloc[-1]['high']
    
    c2_close = df_ltf.iloc[-2]['close']
    c2_open = df_ltf.iloc[-2]['open']

    if trend == 'BULLISH' and c2_close > c2_open and c3_low > c1_high:
        return 'BULLISH', c1_high, c3_low

    if trend == 'BEARISH' and c2_close < c2_open and c3_high < c1_low:
        return 'BEARISH', c3_high, c1_low

    return None, None, None

def main():
    print(f"🚀 SMC Discord Bot Online! Monitoring: {SYMBOL}...")
    requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🚀 **SMC High-Probability Bot Online!** Monitoring `{SYMBOL}` ({HTF} Trend -> {LTF} Entry)"})
    
    last_signal_time = None

    while True:
        try:
            df_htf = fetch_data(SYMBOL, HTF)
            df_ltf = fetch_data(SYMBOL, LTF)

            htf_trend = get_htf_trend(df_htf)
            fvg_type, zone_bottom, zone_top = check_ltf_fvg(df_ltf, htf_trend)

            current_price = df_ltf.iloc[-1]['close']
            current_time = df_ltf.iloc[-1]['timestamp']

            if fvg_type and current_time != last_signal_time:
                send_discord_alert(fvg_type, SYMBOL, htf_trend, LTF, zone_bottom, zone_top, current_price)
                last_signal_time = current_time

            print(f"Monitoring... {SYMBOL} | Price: ${current_price:.2f} | HTF Trend: {htf_trend}")
            time.sleep(60)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == '__main__':
    main()
