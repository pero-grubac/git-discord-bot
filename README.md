# 🤖 GitHub Discord Bot

A personal Discord bot that integrates with GitHub to manage issues, track activity, and generate reports — all from Discord.

## 📁 Project Structure

```
discord-bot/
├── .env
├── .gitignore
├── requirements.txt
├── render.yaml
├── Procfile
├── main.py
├── config.py
└── cogs/
    ├── issues.py       # Issue management commands
    ├── webhook.py      # GitHub → Discord webhook receiver
    ├── stats.py        # Activity stats and monthly reports
    └── activity.py     # Streak, top repo
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
- `/sync-repos` — Sync all GitHub repos to database (adds new ones automatically)
- `/repo-info` — Show repo details (language, stars, forks, open issues, last push)

### Stats & Reports

- `/stats` — Show commit and issue activity (last 7 days / this month / last month)
- `/streak` — Show current and longest commit streak (last 90 days)
- `/top-repo` — Show most active repo this month
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

### 5. Discord bot setup

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → New Application
2. Under **Bot** → enable **Message Content Intent**
3. Under **OAuth2 → URL Generator** → select `bot` scope + permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `View Channels`
4. Open the generated URL and add the bot to your server

### 6. GitHub webhook setup

1. Go to your repo → **Settings → Webhooks → Add webhook**
2. Payload URL: `https://your-render-url.onrender.com/webhook`
3. Content type: `application/json`
4. Secret: same value as `GITHUB_WEBHOOK_SECRET` in `.env`
5. Events: select **Issues** only

### 7. Run the bot

```bash
python main.py
```

## ☁️ Deploy to Render

1. Push the repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — just fill in the environment variables
5. Update your GitHub webhook URL to the Render URL