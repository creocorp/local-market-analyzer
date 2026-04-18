import os
from dotenv import load_dotenv

load_dotenv()

# --- Market Settings ---
DEFAULT_SYMBOL = os.getenv("SYMBOL", "AAPL")
DEFAULT_INTERVAL = os.getenv("INTERVAL", "1d")
DEFAULT_PERIOD = os.getenv("PERIOD", "6mo")

SYMBOLS = os.getenv("SYMBOLS", "AAPL,MSFT,TSLA").split(",")

# --- LLM Settings (Ollama) ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:14b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# --- Technical Indicator Settings ---
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
MACD_FAST = int(os.getenv("MACD_FAST", "12"))
MACD_SLOW = int(os.getenv("MACD_SLOW", "26"))
MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "9"))
BB_PERIOD = int(os.getenv("BB_PERIOD", "20"))
BB_STD = int(os.getenv("BB_STD", "2"))
SMA_SHORT = int(os.getenv("SMA_SHORT", "20"))
SMA_LONG = int(os.getenv("SMA_LONG", "50"))

# --- Signal Thresholds ---
RSI_OVERSOLD = float(os.getenv("RSI_OVERSOLD", "30"))
RSI_OVERBOUGHT = float(os.getenv("RSI_OVERBOUGHT", "70"))
