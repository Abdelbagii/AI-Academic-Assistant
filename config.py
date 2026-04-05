import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-5.4")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

APP_DB_PATH = os.getenv("APP_DB_PATH", "data/app.db")
APP_DB_PATH = os.path.join(BASE_DIR, APP_DB_PATH)

EXPORT_DIR = os.getenv("EXPORT_DIR", "data/exports")
EXPORT_DIR = os.path.join(BASE_DIR, EXPORT_DIR)

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
TOP_K = int(os.getenv("TOP_K", "5"))