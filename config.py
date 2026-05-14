import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SERVER_ID = int(os.getenv("SERVER_ID"))
DISCORD_ISSUE_CHANNEL_ID = int(os.getenv("DISCORD_ISSUE_CHANNEL_ID"))
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
DISCORD_STATS_CHANNEL_ID = os.getenv("GITHUB_WEBHOOK_SECRET")

GITHUB_API = "https://api.github.com"

LABEL_KEYWORDS = {
    "bug": ["bug", "error", "fix", "crash", "ne radi", "broken"],
    "enhancement": ["dodati", "add", "improve", "nova", "new", "feature"],
    "documentation": ["readme", "docs", "dokumentacija", "documentation"],
}
