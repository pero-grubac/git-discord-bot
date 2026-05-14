import hashlib
import hmac
import threading

from discord.ext import commands
from flask import Flask, request, jsonify

from config import DISCORD_ISSUE_CHANNEL_ID, GITHUB_WEBHOOK_SECRET

flask_app = Flask(__name__)
bot_instance = None


def verify_signature(payload: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@flask_app.route("/webhook", methods=["POST"])
def github_webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.headers.get("X-GitHub-Event")
    data = request.json

    if event == "issues" and data.get("action") == "closed":
        issue = data["issue"]
        repo = data["repository"]["name"]
        title = issue["title"]
        number = issue["number"]
        url = issue["html_url"]

        if bot_instance:
            channel = bot_instance.get_channel(DISCORD_ISSUE_CHANNEL_ID)
            if channel:
                import asyncio
                asyncio.run_coroutine_threadsafe(
                    channel.send(f"✅ Issue #{number} closed in `{repo}` — **{title}**\n🔗 {url}"),
                    bot_instance.loop
                )

    return jsonify({"ok": True}), 200


def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)


class Webhook(commands.Cog):
    def __init__(self, bot):
        global bot_instance
        bot_instance = bot
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()


async def setup(bot):
    await bot.add_cog(Webhook(bot))
