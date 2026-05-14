import asyncio
from datetime import datetime, timezone, timedelta

import discord
import requests
from discord import app_commands
from discord.ext import commands

from config import *


def get_commit_days(days: int = 90) -> set:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    since = datetime.now(timezone.utc) - timedelta(days=days)
    commit_days = set()
    repos_url = f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos?per_page=100"
    repos = requests.get(repos_url, headers=headers, timeout=5).json()

    for repo in repos:
        repo_name = repo["name"]
        url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo_name}/commits"
        params = {
            "author": GITHUB_USERNAME,
            "since": since.isoformat(),
            "per_page": 100,
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            for commit in response.json():
                date_str = commit["commit"]["author"]["date"][:10]
                commit_days.add(date_str)

    return commit_days


def calculate_streak(commit_days: set) -> tuple[int, int]:
    today = datetime.now(timezone.utc).date()
    current_streak = 0
    longest_streak = 0
    temp = 0

    # Current streak
    day = today
    while str(day) in commit_days:
        current_streak += 1
        day -= timedelta(days=1)

    # If no commit today, check yesterday
    if current_streak == 0:
        day = today - timedelta(days=1)
        while str(day) in commit_days:
            current_streak += 1
            day -= timedelta(days=1)

    # Longest streak in last 90 days
    for i in range(90):
        day = str(today - timedelta(days=i))
        if day in commit_days:
            temp += 1
            longest_streak = max(longest_streak, temp)
        else:
            temp = 0

    return current_streak, longest_streak


def get_top_repo(since: datetime) -> dict | None:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    repos = requests.get(
        f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos?per_page=100",
        headers=headers,
        timeout=5
    ).json()

    top = None
    top_count = 0

    for repo in repos:
        repo_name = repo["name"]
        url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo_name}/commits"
        params = {
            "author": GITHUB_USERNAME,
            "since": since.isoformat(),
            "per_page": 100,
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            count = len(response.json())
            if count > top_count:
                top_count = count
                top = {"name": repo_name, "count": count, "url": repo["html_url"]}

    return top


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="streak", description="Show your current commit streak")
    async def streak(self, interaction: discord.Interaction):
        await interaction.response.defer()

        loop = asyncio.get_event_loop()
        commit_days = await loop.run_in_executor(None, get_commit_days, 90)
        current, longest = calculate_streak(commit_days)

        fire = "🔥" * min(current, 5) if current > 0 else "😴"
        lines = [
            f"## {fire} Commit Streak",
            f"**Current streak:** {current} day{'s' if current != 1 else ''}",
            f"**Longest streak (90 days):** {longest} day{'s' if longest != 1 else ''}",
        ]

        if current == 0:
            lines.append("\n> No commits today or yesterday. Get back to it! 💪")
        elif current >= 7:
            lines.append(f"\n> {current} days in a row. Keep it up! 🚀")

        await interaction.followup.send("\n".join(lines))

    @app_commands.command(name="top-repo", description="Show most active repo this month")
    async def top_repo(self, interaction: discord.Interaction):
        await interaction.response.defer()

        now = datetime.now(timezone.utc)
        since = now.replace(day=1, hour=0, minute=0, second=0)

        loop = asyncio.get_event_loop()
        top = await loop.run_in_executor(None, get_top_repo, since)

        if not top:
            await interaction.followup.send("😴 No commits this month.")
            return

        month = now.strftime("%B %Y")
        await interaction.followup.send(
            f"## 🏆 Top repo — {month}\n"
            f"**`{top['name']}`** — {top['count']} commit{'s' if top['count'] != 1 else ''}\n"
            f"🔗 {top['url']}"
        )


async def setup(bot):
    await bot.add_cog(Activity(bot))
