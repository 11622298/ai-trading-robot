import time
import random
import requests
import threading
from datetime import datetime
from flask import Flask, request
import json

# === Configuration ===
BOT_TOKEN = '7665409371:AAEF9qgNVufWKbD9hH7QVUk4iv6UwhQv0ro'
CHAT_ID = '6610385047'
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# === Flask App ===
app = Flask(__name__)

# === Bot State ===
market_type = "Forex"
symbol = "EURUSD"
otc_mode = False
trade_memory = []
MEMORY_FILE = "memory.json"

# === Load Memory if Exists ===
def load_memory():
    global trade_memory
    try:
        with open(MEMORY_FILE, 'r') as f:
            trade_memory = json.load(f)
    except:
        trade_memory = []

# === Save Memory ===
def save_memory():
    with open(MEMORY_FILE, 'w') as f:
        json.dump(trade_memory, f, indent=2)

# === Simulate Trend ===
def get_mock_trend():
    return random.choice(["Uptrend", "Downtrend", "Sideways"])

# === Analyze Memory for Smart Suggestions ===
def generate_ai_suggestion():
    if not trade_memory:
        return "No past trades to analyze yet."

    hours = {}
    trends = {}
    wins = 0
    total = 0

    for trade in trade_memory:
        hour = trade['time'].split()[1][:2]
        trend = trade['trend']
        result = trade['result']

        hours[hour] = hours.get(hour, 0) + (1 if result == "win" else 0)
        trends[trend] = trends.get(trend, 0) + (1 if result == "win" else 0)
        total += 1
        if result == "win":
            wins += 1

    best_hour = max(hours, key=hours.get)
    best_trend = max(trends, key=trends.get)
    win_rate = (wins / total) * 100

    return f"🧠 AI Suggestion:\nBest hour: {best_hour}:00\nBest trend: {best_trend}\nWin rate: {win_rate:.1f}%\nSymbol: {symbol}\nMarket Type: {market_type}\nTry trading in similar conditions."

# === Send Inline Keyboard Message ===
def send_message(text):
    keyboard = [
        [
            {"text": "Forex", "callback_data": "set_market_Forex"},
            {"text": "Crypto", "callback_data": "set_market_Crypto"},
            {"text": "Indices", "callback_data": "set_market_Indices"},
            {"text": "Stocks", "callback_data": "set_market_Stocks"}
        ],
        [
            {"text": "EURUSD", "callback_data": "set_symbol_EURUSD"},
            {"text": "BTCUSD", "callback_data": "set_symbol_BTCUSD"},
            {"text": "US30", "callback_data": "set_symbol_US30"},
            {"text": "AAPL", "callback_data": "set_symbol_AAPL"}
        ],
        [
            {"text": "BUY", "callback_data": "trade_BUY"},
            {"text": "SELL", "callback_data": "trade_SELL"}
        ],
        [
            {"text": "Toggle OTC", "callback_data": "toggle_otc"},
            {"text": "Suggest", "callback_data": "suggest"}
        ]
    ]
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "reply_markup": {"inline_keyboard": keyboard}
    }
    requests.post(f"{URL}/sendMessage", json=payload)

# === Save Each Trade Entry ===
def log_trade(direction, trend, result):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {
        "time": now,
        "market": market_type,
        "symbol": symbol,
        "direction": direction,
        "trend": trend,
        "result": result,
        "otc": otc_mode
    }
    trade_memory.append(entry)
    save_memory()

# === Answer Callback ===
def answer_callback(callback_id):
    requests.post(f"{URL}/answerCallbackQuery", json={"callback_query_id": callback_id})

# === Handle Telegram Updates ===
def get_updates(offset=None):
    params = {"timeout": 100, "offset": offset}
    res = requests.get(f"{URL}/getUpdates", params=params)
    return res.json()

# === Handle Incoming Webhook from TradingView ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    direction = data.get("action")
    asset = data.get("symbol")
    reason = data.get("reason", "TradingView Alert")

    trend = get_mock_trend()
    result = random.choice(["win", "loss"])
    log_trade(direction, trend, result)

    message = f"📡 TradingView Signal Received:\nAction: {direction}\nAsset: {asset}\nTrend: {trend}\nReason: {reason}\nResult: {result}"
    send_message(message)
    return "Signal received", 200

# === Run Bot Thread ===
def run_bot():
    load_memory()
    last_update_id = None
    send_message("🤖 AI Trading Bot Ready. Choose a market, asset, or make a trade.")

    while True:
        updates = get_updates(last_update_id)
        if "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1
                callback = update.get("callback_query")
                if callback:
                    callback_id = callback["id"]
                    data = callback["data"]
                    chat_id = callback["message"]["chat"]["id"]
                    answer_callback(callback_id)

                    global market_type, symbol, otc_mode

                    if data.startswith("set_market_"):
                        market_type = data.replace("set_market_", "")
                        send_message(f"📊 Market type set to: {market_type}")

                    elif data.startswith("set_symbol_"):
                        symbol = data.replace("set_symbol_", "")
                        send_message(f"💱 Symbol set to: {symbol}")

                    elif data == "toggle_otc":
                        otc_mode = not otc_mode
                        send_message(f"🔄 OTC Mode {'Enabled' if otc_mode else 'Disabled'}")

                    elif data.startswith("trade_"):
                        direction = data.replace("trade_", "")
                        trend = get_mock_trend()
                        result = random.choice(["win", "loss"])
                        log_trade(direction, trend, result)
                        send_message(f"📈 Trade Logged:\nMarket: {market_type}\nSymbol: {symbol}\nDirection: {direction}\nTrend: {trend}\nResult: {result}\nOTC: {otc_mode}")

                    elif data == "suggest":
                        suggestion = generate_ai_suggestion()
                        send_message(suggestion)

        time.sleep(1)

# === Start Flask + Bot ===
if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=5000)
