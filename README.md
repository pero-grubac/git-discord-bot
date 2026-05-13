# 🤖 GitHub Discord Bot

A personal Discord bot that integrates with GitHub to manage issues, track activity, and generate reports — all from Discord.

## 📁 Project Structure

```
discord-bot/
├── .env
├── .gitignore
├── requirements.txt
├── main.py
├── config.py
└── cogs/
    ├── issues.py       # Issue management commands
    ├── webhook.py      # GitHub → Discord webhook receiver
    └── stats.py        # Activity stats and monthly reports
```

## ✨ Features

### Issue Management
- `/add` — Create a GitHub issue with title, description, and label (autocomplete for repos and labels)
- `/list` — Show all open issues across registered repos
- `/done` — Close a GitHub issue directly from Discord
- `/today` — Show issues created today

### Repo Management
- `/repos` — List all registered repos
- `/register` — Register a new GitHub repo (validates against GitHub API)

### Stats & Reports
- `/stats` — Show commit and issue activity (last 7 days / this month / last month)
- 📅 Automatic monthly report sent to a dedicated Discord channel

### GitHub → Discord Notifications
- Webhook integration: closing an issue on GitHub sends a notification to Discord automatically

## 🛠️ Stack

- **Python** — discord.py, Flask
- **Supabase** — PostgreSQL (repos, issues, time_logs)
- **GitHub REST API** — Issues, Commits, Search
- **Render** — Deployment
- **ngrok** — Local webhook testing

## 🚀 Getting Started

### 1. Clone the repo
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
SERVER_ID=
DISCORD_ISSUE_CHANNEL_ID=
DISCORD_STATS_CHANNEL_ID=
GITHUB_TOKEN=
GITHUB_USERNAME=
GITHUB_WEBHOOK_SECRET=
SUPABASE_URL=
SUPABASE_KEY=
```

### 4. Set up Supabase
Run the following SQL in your Supabase SQL Editor:
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

### 5. Run the bot
```bash
python main.py
```



