import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
ORIGIN = os.getenv("ORIGIN", "LHE")
DESTINATION = os.getenv("DESTINATION", "DXB")
MAX_PRICE = float(os.getenv("MAX_PRICE", "300"))