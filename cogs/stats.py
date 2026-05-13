import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
import requests
from config import *
import asyncio


def fetch_repo_commits(args):
    repo_name, since, until, headers = args
    try:
        commits_url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo_name}/commits"
        params = {
            "author": GITHUB_USERNAME,
            "since": since.isoformat(),
            "until": until.isoformat(),
            "per_page": 100,
        }
        response = requests.get(commits_url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            commits = response.json()
            if commits:
                return repo_name, {
                    "count": len(commits),
                    "titles": [c["commit"]["message"].split("\n")[0] for c in commits]
                }
    except Exception:
        pass
    return repo_name, None


def get_commit_stats(since: datetime, until: datetime) -> dict:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    repos_url = f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos?per_page=100"
    repos = requests.get(repos_url, headers=headers, timeout=5).json()

    args = [(repo["name"], since, until, headers) for repo in repos]

    stats = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for repo_name, data in executor.map(fetch_repo_commits, args):
            if data:
                stats[repo_name] = data

    return stats


def get_issue_stats(since: datetime, until: datetime) -> dict:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    since_str = since.strftime("%Y-%m-%d")
    until_str = until.strftime("%Y-%m-%d")
    search_url = f"{GITHUB_API}/search/issues"

    opened = requests.get(search_url, headers=headers, timeout=5, params={
        "q": f"author:{GITHUB_USERNAME} type:issue created:{since_str}..{until_str}",
        "per_page": 100,
    }).json()

    closed = requests.get(search_url, headers=headers, timeout=5, params={
        "q": f"author:{GITHUB_USERNAME} type:issue closed:{since_str}..{until_str}",
        "per_page": 100,
    }).json()

    def group_by_repo(items):
        result = {}
        for item in items:
            repo = item["repository_url"].split("/")[-1]
            if repo not in result:
                result[repo] = []
            result[repo].append(item["title"])
        return result

    return {
        "opened": opened.get("total_count", 0),
        "closed": closed.get("total_count", 0),
        "opened_by_repo": group_by_repo(opened.get("items", [])),
        "closed_by_repo": group_by_repo(closed.get("items", [])),
    }


def build_report(commit_stats: dict, issue_stats: dict, label: str) -> str:
    total_commits = sum(v["count"] for v in commit_stats.values())
    total_opened = issue_stats["opened"]
    total_closed = issue_stats["closed"]

    lines = [f"## 📊 {label}", ""]

    if total_commits == 0 and total_opened == 0 and total_closed == 0:
        lines.append("😴 No activity this period.")
        return "\n".join(lines)

    all_repos = sorted(set(
        list(commit_stats.keys()) +
        list(issue_stats["opened_by_repo"].keys()) +
        list(issue_stats["closed_by_repo"].keys())
    ))

    for repo in all_repos:
        lines.append(f"### 📁 `{repo}`")

        if repo in commit_stats:
            count = commit_stats[repo]["count"]
            lines.append(f"🔨 **Commits — {count}**")
            for title in commit_stats[repo]["titles"]:
                lines.append(f"> • {title}")

        if repo in issue_stats["opened_by_repo"]:
            count = len(issue_stats["opened_by_repo"][repo])
            lines.append(f"🟢 **Issues opened — {count}**")
            for title in issue_stats["opened_by_repo"][repo]:
                lines.append(f"> • {title}")

        if repo in issue_stats["closed_by_repo"]:
            count = len(issue_stats["closed_by_repo"][repo])
            lines.append(f"✅ **Issues closed — {count}**")
            for title in issue_stats["closed_by_repo"][repo]:
                lines.append(f"> • {title}")

        lines.append("")

    lines.append(f"**Total — 🔨 {total_commits} commits · 🟢 {total_opened} opened · ✅ {total_closed} closed**")

    return "\n".join(lines)


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monthly_report.start()

    def cog_unload(self):
        self.monthly_report.cancel()

    @tasks.loop(hours=24)
    async def monthly_report(self):
        now = datetime.now(timezone.utc)
        if now.day != 1 or now.hour != 9:
            return

        since = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        until = now.replace(day=1)
        label = since.strftime("Monthly report — %B %Y")

        commit_stats = get_commit_stats(since, until)
        issue_stats = get_issue_stats(since, until)
        report = build_report(commit_stats, issue_stats, label)

        channel = self.bot.get_channel(DISCORD_STATS_CHANNEL_ID)
        if channel:
            await channel.send(report)

    @monthly_report.before_loop
    async def before_monthly_report(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="stats", description="Show commit and issue stats")
    @app_commands.choices(period=[
        app_commands.Choice(name="This week", value="week"),
        app_commands.Choice(name="This month", value="month"),
        app_commands.Choice(name="Last month", value="last_month"),
    ])
    async def stats(self, interaction: discord.Interaction, period: str = "week"):
        await interaction.response.defer()

        now = datetime.now(timezone.utc)

        if period == "week":
            since = now - timedelta(days=7)
            until = now
            label = "Stats — last 7 days"
        elif period == "month":
            since = now.replace(day=1, hour=0, minute=0, second=0)
            until = now
            label = now.strftime("Stats — %B %Y")
        else:
            first_this = now.replace(day=1, hour=0, minute=0, second=0)
            since = (first_this - timedelta(days=1)).replace(day=1)
            until = first_this
            label = since.strftime("Stats — %B %Y")

        loop = asyncio.get_event_loop()
        commit_stats, issue_stats = await asyncio.gather(
            loop.run_in_executor(None, get_commit_stats, since, until),
            loop.run_in_executor(None, get_issue_stats, since, until),
        )

        report = build_report(commit_stats, issue_stats, label)
        await interaction.followup.send(report)


async def setup(bot):
    await bot.add_cog(Stats(bot))