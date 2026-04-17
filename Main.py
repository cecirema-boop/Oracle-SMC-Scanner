import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOLS = ["NAS100", "NQ=F", "GC=F", "^DJI"] # NAS100, Gold, US30

def send_signal(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def get_data(symbol):
    # Fetching 15m data for SMC setups
    df = yf.download(symbol, period="2d", interval="15m", progress=False)
    return df

def scan_logic():
    for sym in SYMBOLS:
        df = get_data(sym)
        if df.empty: continue

        # Technicals
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last_close = df['Close'].iloc[-1]
        prev_low = df['Low'].iloc[-5:-1].min()
        prev_high = df['High'].iloc[-5:-1].max()
        
        # --- SMC LOGIC: LIQUIDITY SWEEP ---
        # BUY: Price dips below previous low (Sweep) then closes above it
        if df['Low'].iloc[-1] < prev_low and last_close > prev_low:
            if last_close > df['EMA_200'].iloc[-1]: # Trend Filter
                msg = f"🎯 *ORACLE SIGNAL: {sym}*\n\n" \
                      f"🔥 *Action:* BUY (Liquidity Sweep) 📈\n" \
                      f"📍 *Entry:* {round(last_close, 2)}\n" \
                      f"🛡️ *SL:* {round(df['Low'].iloc[-1], 2)}\n" \
                      f"💰 *TP:* {round(last_close + (last_close - df['Low'].iloc[-1])*3, 2)}\n\n" \
                      f"🧠 *Logic:* Banks just hunted retail stops. Trend is Bullish."
                send_signal(msg)

        # SELL: Price sweeps high then closes below
        elif df['High'].iloc[-1] > prev_high and last_close < prev_high:
            if last_close < df['EMA_200'].iloc[-1]:
                msg = f"🎯 *ORACLE SIGNAL: {sym}*\n\n" \
                      f"🔥 *Action:* SELL (Liquidity Sweep) 📉\n" \
                      f"📍 *Entry:* {round(last_close, 2)}\n" \
                      f"🛡️ *SL:* {round(df['High'].iloc[-1], 2)}\n" \
                      f"💰 *TP:* {round(last_close - (df['High'].iloc[-1] - last_close)*3, 2)}\n\n" \
                      f"🧠 *Logic:* Liquidity grabbed at the highs. Trend is Bearish."
                send_signal(msg)

# --- EXECUTION LOOP ---
print("Oracle SMC Bot is Live... Scanning.")
send_signal("🚀 *Oracle Bot Connected.* Monitoring NAS100, Gold, and US30.")

while True:
    try:
        scan_logic()
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(900) # Scan every 15 mins (new candle)
