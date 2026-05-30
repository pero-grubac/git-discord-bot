<div align="center">

# 🤖 GitHub Discord Bot

![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.3-5865f2?style=flat-square&logo=discord&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3fcf8e?style=flat-square&logo=supabase&logoColor=white)
![GitHub API](https://img.shields.io/badge/GitHub_API-REST-181717?style=flat-square&logo=github&logoColor=white)
![Render](https://img.shields.io/badge/Render-deployed-46e3b7?style=flat-square&logo=render&logoColor=white)

</div>

---

## 📌 Project Overview

**GitHub Discord Bot** is a personal productivity bot that bridges Discord and GitHub. Manage issues, track commit activity, and receive automated reports — all without leaving Discord. Built for solo developers who want a lightweight command center for their GitHub workflow.

---

## ✨ Features

### Issue Management
- `/add` — Create a GitHub issue with title, description, and label (autocomplete for repos and labels)
- `/list` — Show all open issues across registered repos
- `/done` — Close a GitHub issue directly from Discord
- `/today` — Show issues created today

### Repo Management
- `/repos` — List all registered repos
- `/register` — Register a GitHub repo (validates against GitHub API)
- `/sync-repos` — Sync all GitHub repos to database at once
- `/repo-info` — Show repo details (language, stars, forks, open issues, last push)

### Activity & Stats
- `/stats` — Commit and issue breakdown (last 7 days / this month / last month)
- `/streak` — Current and longest commit streak (last 90 days)
- `/heatmap` — Commit activity grid for the last 15 weeks
- `/top-repo` — Most active repo this month
- 📅 Automatic monthly report posted to a dedicated Discord channel

### GitHub → Discord Notifications
- Webhook integration: closing an issue on GitHub triggers an instant Discord notification

---

## 🛠️ Tech Stack

| Technology | Usage |
|------------|-------|
| Python 3.11 | Core language |
| discord.py 2.3 | Discord bot framework (slash commands, Cogs) |
| Flask 3.1 | Webhook HTTP receiver |
| Supabase | PostgreSQL — repos, issues, time_logs |
| GitHub REST API | Issues, Commits, Search |
| Render | Cloud deployment |
| ngrok | Local webhook testing |

---

## 📁 Project Structure

```
discord-bot/
├── .env
├── .gitignore
├── requirements.txt
├── runtime.txt
├── render.yaml
├── Procfile
├── main.py                 # Bot entry point, Cog loader, command tree sync
├── config.py               # Environment variables, label keywords
└── cogs/
    ├── issues.py           # Issue and repo management commands
    ├── webhook.py          # Flask server, GitHub webhook receiver
    ├── stats.py            # Stats commands, monthly report task
    └── activity.py         # Streak, heatmap, top-repo commands
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A Discord server where you have admin access
- A GitHub account with a personal access token (fine-grained, Issues: read/write)
- A Supabase project

### 1. Clone the repository

```bash
git clone https://github.com/pero-grubac/discord-bot
cd discord-bot
```

### 2. Create virtual environment

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/macOS
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=
GUILD_ID=
DISCORD_CHANNEL_ID=
DISCORD_STATS_CHANNEL_ID=
GITHUB_TOKEN=
GITHUB_USERNAME=
GITHUB_WEBHOOK_SECRET=
SUPABASE_URL=
SUPABASE_KEY=
```

### 4. Set up Supabase

Run the following SQL in your Supabase **SQL Editor**:

```sql
create table repos (
  id serial primary key,
  name text not null unique,
  private boolean default false
);

create table issues (
  id serial primary key,
  discord_msg_id text unique,
  repo_name text references repos(name),
  github_issue_number integer not null,
  title text not null,
  labels text[] default '{}',
  status text default 'open' check (status in ('open', 'closed')),
  created_at timestamptz default now()
);

create table time_logs (
  id serial primary key,
  task_name text not null,
  repo_name text references repos(name),
  started_at timestamptz not null,
  stopped_at timestamptz
);
```

### 5. Discord bot setup

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → **New Application**
2. Under **Bot** → enable **Message Content Intent**
3. Under **OAuth2 → URL Generator** → select `bot` scope with permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `View Channels`
4. Open the generated URL and add the bot to your server

### 6. GitHub webhook setup

1. Go to your repo → **Settings → Webhooks → Add webhook**
2. **Payload URL:** `https://your-render-url.onrender.com/webhook`
3. **Content type:** `application/json`
4. **Secret:** same value as `GITHUB_WEBHOOK_SECRET` in `.env`
5. **Events:** select **Issues** only

### 7. Run the bot

```bash
python main.py
```

---

## ☁️ Deploy to Render

1. Push the repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo — Render auto-detects `render.yaml`
4. Fill in environment variables under **Environment**
5. Set `PYTHON_VERSION` to `3.11.9`
6. Update your GitHub webhook Payload URL to the Render URL

To keep the service alive on the free tier, set up a monitor on [uptimerobot.com](https://uptimerobot.com) pointing to `https://your-render-url.onrender.com/health` with a 5-minute interval.

---

## ⚠️ Known Limitations

- GitHub API returns max 100 commits per request — repos with very high commit volume in a single period may show incomplete counts
- Render free tier spins down after 15 minutes of inactivity — UptimeRobot ping is required to keep the bot online
- Slash command sync on startup adds ~5–10 seconds to bot startup time
- GitHub account-level webhooks are not available for individual users — webhooks must be configured per repo
