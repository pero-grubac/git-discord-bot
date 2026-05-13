import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client
from config import *
import requests

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def detect_labels(text: str) -> list[str]:
    text_lower = text.lower()
    return [
        label for label, keywords in LABEL_KEYWORDS.items()
        if any(kw in text_lower for kw in keywords)
    ]


def create_github_issue(repo: str, title: str, labels: list[str], description: str = None) -> dict:
    url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "title": title,
        "labels": labels,
        "assignees": [GITHUB_USERNAME],
    }
    if description:
        payload["body"] = description

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


async def repo_autocomplete(interaction: discord.Interaction, current: str):
    result = supabase.table("repos").select("name").execute()
    return [
        app_commands.Choice(name=r["name"], value=r["name"])
        for r in result.data
        if current.lower() in r["name"].lower()
    ][:25]

async def label_autocomplete(interaction: discord.Interaction, current: str):
    labels = list(LABEL_KEYWORDS.keys())
    return [
        app_commands.Choice(name=l, value=l)
        for l in labels
        if current.lower() in l.lower()
    ]

class Issues(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add", description="Create a new GitHub issue")
    @app_commands.autocomplete(repo=repo_autocomplete, label=label_autocomplete)
    async def add_issue(
            self,
            interaction: discord.Interaction,
            repo: str,
            title: str,
            description: str ,
            label: str
    ):
        await interaction.response.defer()

        result = supabase.table("repos").select("name").eq("name", repo).execute()
        if not result.data:
            await interaction.followup.send(f"❌ Repo `{repo}` not found. Use `/repos` to see available repos.")
            return

        labels = detect_labels(title)
        if label and label not in labels:
            labels.append(label)

        try:
            issue = create_github_issue(repo, title, labels, description)
        except Exception as e:
            await interaction.followup.send(f"❌ GitHub error: {e}")
            return

        supabase.table("issues").insert({
            "discord_msg_id": str(interaction.id),
            "repo_name": repo,
            "github_issue_number": issue["number"],
            "title": title,
            "labels": labels,
        }).execute()

        label_str = f" `{'` `'.join(labels)}`" if labels else ""
        await interaction.followup.send(
            f"✅ Issue #{issue['number']} created in `{repo}`{label_str}\n"
            f"🔗 {issue['html_url']}"
        )

    @app_commands.command(name="list", description="Show all open tasks")
    async def list_issues(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = supabase.table("issues").select("*").eq("status", "open").order("created_at").execute()
        if not result.data:
            await interaction.followup.send("📭 No open tasks.")
            return

        lines = ["**Open tasks:**"]
        for issue in result.data:
            labels = f" `{'` `'.join(issue['labels'])}`" if issue["labels"] else ""
            lines.append(f"`#{issue['github_issue_number']}` **{issue['repo_name']}** — {issue['title']}{labels}")

        await interaction.followup.send("\n".join(lines))

    @app_commands.command(name="done", description="Close a GitHub issue by number")
    @app_commands.autocomplete(repo=repo_autocomplete)
    async def close_issue(self, interaction: discord.Interaction, repo: str, issue_number: int):
        await interaction.response.defer()
        result = supabase.table("issues").select("*").eq("github_issue_number", issue_number).eq("repo_name", repo).eq("status", "open").execute()
        if not result.data:
            await interaction.followup.send(f"❌ Issue #{issue_number} not found in `{repo}`.")
            return

        issue = result.data[0]

        url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo}/issues/{issue_number}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        requests.patch(url, json={"state": "closed"}, headers=headers)

        supabase.table("issues").update({"status": "closed"}).eq("github_issue_number", issue_number).eq("repo_name", repo).execute()

        await interaction.followup.send(f"✅ Issue #{issue_number} closed — `{issue['title']}`")

    @app_commands.command(name="today", description="Show tasks created today")
    async def today_issues(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = supabase.table("issues").select("*").gte("created_at", today).execute()

        if not result.data:
            await interaction.followup.send("📭 No tasks created today.")
            return

        lines = ["**Tasks added today:**"]
        for issue in result.data:
            status = "✅" if issue["status"] == "closed" else "🔵"
            lines.append(f"{status} `#{issue['github_issue_number']}` **{issue['repo_name']}** — {issue['title']}")

        await interaction.followup.send("\n".join(lines))

    @app_commands.command(name="repos", description="List all registered repos")
    async def list_repos(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = supabase.table("repos").select("name, private").execute()
        if not result.data:
            await interaction.followup.send("📭 No repos registered. Use `/register` to add one.")
            return

        lines = ["**Available repos:**"]
        for repo in result.data:
            lock = "🔒" if repo["private"] else "🌐"
            lines.append(f"{lock} `{repo['name']}`")

        await interaction.followup.send("\n".join(lines))

    @app_commands.command(name="register", description="Register a GitHub repo")
    async def register_repo(self, interaction: discord.Interaction, repo: str, private: bool = False):
        await interaction.response.defer()

        # Check if repo exists on GitHub
        url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            await interaction.followup.send(f"❌ Repo `{repo}` not found on GitHub.")
            return

        # Check if already registered
        existing = supabase.table("repos").select("name").eq("name", repo).execute()
        if existing.data:
            await interaction.followup.send(f"⚠️ Repo `{repo}` is already registered.")
            return

        supabase.table("repos").insert({"name": repo, "private": private}).execute()
        lock = "🔒" if private else "🌐"
        await interaction.followup.send(f"{lock} Repo `{repo}` registered successfully.")


async def setup(bot):
    await bot.add_cog(Issues(bot))