# Velvet

A Telegram bot that sells paid access to a private channel. Payments are handled via
[CryptoBot (Crypto Pay API)](https://help.crypt.bot/crypto-pay-api) in **USDT** and **TON**.
Subscriptions are managed automatically — when a subscription expires, the bot removes
the user from the channel on its own.

## Features

- 📲 `/start` menu with a welcome image and inline buttons: Get Access, How It Works, Support, My Subscription.
- 💳 Two payment methods via CryptoBot: direct invoice or mini-app — both links are generated automatically.
- 🧾 Flexible plans (duration, price, title) configured via JSON in `.env`.
- 🔐 One-time invite links (`member_limit = 1`) for each new subscription — the link can't be shared or reused.
- ⏰ Scheduler: renewal reminders **3 days** and **1 day** before expiry (configurable), automatic kick after expiry.
- 🛡 Abuse protection: global anti-flood + per-minute purchase limit, HMAC webhook signature verification, idempotent payment activation.
- 📊 Admin panel `/admin`: user count, active subscriptions, total payments, revenue by currency, per-plan breakdown, recent subscriptions.
- 💰 **Prices can be changed directly from the admin panel** — no redeploy, no `.env` edits. Existing subscriptions and invoices keep their original price.
- 🐳 Docker, Docker Compose, Alembic migrations, and unit tests included.

## Table of Contents

- [Quick Start](#quick-start)
- [Creating and Configuring Bots](#creating-and-configuring-bots)
- [Configuration](#configuration)
- [Running](#running)
- [Crypto Pay Webhook](#crypto-pay-webhook)
- [Architecture](#architecture)
- [Bot Commands](#bot-commands)
- [Database and Migrations](#database-and-migrations)
- [Testing and Code Style](#testing-and-code-style)
- [Deployment](#deployment) — summary; full guide in [DEPLOY.md](DEPLOY.md)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [License](#license)

---

## Quick Start

```powershell
# Windows PowerShell
git clone https://github.com/your-org/velvet-bot.git
cd velvet-bot

Copy-Item .env.example .env
notepad .env   # fill in your tokens and settings

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

alembic upgrade head
python -m bot
```

```bash
# Linux / macOS
git clone https://github.com/your-org/velvet-bot.git
cd velvet-bot

cp .env.example .env
nano .env   # fill in your tokens and settings

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head
python -m bot
```

Within a few seconds the bot will respond to `/start` in Telegram.

## Creating and Configuring Bots

1. **Telegram bot** — open [@BotFather](https://t.me/BotFather), run `/newbot`, get your `BOT_TOKEN`.
2. **Channel** — create a private channel, add the bot as an administrator with the
   **"Invite users via link"** permission. Find the numeric `chat_id` by forwarding
   any post from the channel to [@userinfobot](https://t.me/userinfobot).
3. **CryptoBot** — open [@CryptoBot](https://t.me/CryptoBot), go to
   `Crypto Pay → My Apps → Create App`. Copy the API token into `CRYPTO_PAY_TOKEN`.
   For testing use `https://testnet-pay.crypt.bot` and [@CryptoTestnetBot](https://t.me/CryptoTestnetBot).
4. **Admins** — find your `user_id` via [@userinfobot](https://t.me/userinfobot)
   and put it in `ADMIN_IDS` (comma-separated for multiple admins).

## Configuration

All settings are read from environment variables or `.env`. A fully commented example
is in [`.env.example`](.env.example).

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `CHANNEL_ID` | Numeric ID of the private channel (negative number) |
| `ADMIN_IDS` | Admin user IDs, comma-separated |
| `CRYPTO_PAY_TOKEN` | Crypto Pay API token |
| `CRYPTO_PAY_BASE_URL` | `https://pay.crypt.bot` (mainnet) or `https://testnet-pay.crypt.bot` |
| `CRYPTO_PAY_ASSETS` | Payment currencies, comma-separated (`USDT,TON`) |
| `SUBSCRIPTION_PLANS` | JSON array of plans (see below) — must be on one line |
| `REMINDER_DAYS` | Days before expiry to send reminders (default `3,1`) |
| `WEBHOOK_ENABLED` | `true` to enable the Crypto Pay HTTP webhook |
| `WEBHOOK_HOST` / `WEBHOOK_PORT` / `WEBHOOK_PATH` | Webhook server settings |
| `POLL_INTERVAL_SECONDS` | Invoice polling interval when webhook is disabled |
| `WELCOME_IMAGE` | Path to the welcome image (or leave empty) |
| `SUPPORT_URL` / `INFO_URL` | URLs for the corresponding menu buttons (optional) |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/bot.sqlite3` or `postgresql+asyncpg://...` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `THROTTLE_BUY_PER_MINUTE` | Max purchase attempts per minute per user |

### Subscription Plans

Must be written as a single line in `.env` (no line breaks):

```
SUBSCRIPTION_PLANS=[{"id":"1m","title":"1 Month","days":30,"price":"5.00"},{"id":"3m","title":"3 Months","days":90,"price":"13.00"},{"id":"6m","title":"6 Months","days":180,"price":"24.00"},{"id":"12m","title":"12 Months","days":365,"price":"42.00"}]
```

- `id` must be unique and stable — it is stored with every payment record. Don't change it for existing plans.
- `price` is the nominal amount in the currency chosen by the user. By default the same number is used for both USDT and TON. To set separate prices per currency, override `SubscriptionService._amount_for`.
- `days` are added on top of the current expiry if the subscription is still active — renewing early doesn't burn remaining days.

### Texts and Branding

All user-facing strings live in `src/bot/texts.py` — edit them directly, no `.po` files needed.
Put your welcome image at `assets/welcome.jpg` and set the path in `WELCOME_IMAGE`.

## Running

### Locally

```powershell
# Windows
pip install -e ".[dev]"
alembic upgrade head
python -m bot
```

```bash
# Linux / macOS
pip install -e ".[dev]"
alembic upgrade head
python -m bot
```

### Docker Compose

```bash
cp .env.example .env
# fill in secrets, configure WEBHOOK_* if needed
docker compose up -d --build
docker compose logs -f
```

The `./data` volume is mapped into the container — this is where the SQLite database and other persisted data live.

## Crypto Pay Webhook

Webhooks are recommended in production — faster and more efficient than polling.

1. Put the bot behind an HTTPS reverse proxy (Caddy, nginx, Cloudflare Tunnel).
2. Set in `.env`:
   ```env
   WEBHOOK_ENABLED=true
   WEBHOOK_HOST=0.0.0.0
   WEBHOOK_PORT=8080
   WEBHOOK_PATH=/cryptopay
   ```
3. In @CryptoBot → Crypto Pay → My Apps → Edit App, set the Webhook URL to
   `https://your-domain.tld/cryptopay`. Enable the `invoice_paid` event.

If the webhook is unavailable, the bot still works: a background job polls invoice statuses every `POLL_INTERVAL_SECONDS` seconds via `getInvoices`.

Each webhook request is verified via HMAC-SHA256 of the SHA-256 hash of your token. The endpoint returns `401` if the signature doesn't match — no data is processed.

## Architecture

```
src/bot/
├── app.py              — bootstrapping: Dispatcher, scheduler, webhook
├── config.py           — pydantic-settings, plans, validation
├── texts.py            — all user-facing strings
├── logger.py           — structlog
├── database/           — SQLAlchemy 2 async, repositories, sessions
├── handlers/           — start, subscription, payment, admin, errors
├── keyboards/          — inline keyboards + typed CallbackData
├── middlewares/        — throttling, DB session injection
├── filters/            — admin filter
├── services/
│   ├── cryptobot.py    — Crypto Pay client + signature verification
│   ├── channel.py      — invite links and channel kick
│   └── subscription.py — purchase / activation / renewal business logic
├── scheduler/          — APScheduler: reminders, kick, invoice polling
└── web/                — aiohttp endpoint for Crypto Pay webhook
```

Purchase flow:

```
user → /start → "Get Access" → plan → currency
                                      ↓
                  CryptoPay.create_invoice  → invoice_id + pay_url + mini_app_url
                                      ↓
                       Payment(status=pending)
                                      ↓
          ┌──────── webhook ────────┐    ┌──── manual "Check Payment" button
          ↓                         ↓    ↓
        invoice_paid              poll job
                                      ↓
             SubscriptionService.activate_paid_invoice
                                      ↓
              Subscription(expires_at = now + plan.days)
                                      ↓
               one-time invite link → user
```

## Bot Commands

| Command   | Who sees it | What it does |
|-----------|-------------|--------------|
| `/start`  | everyone    | Welcome screen, image, main menu |
| `/admin`  | admins only | Stats, breakdowns, recent subscriptions, **live price editing** |

Everything else is handled via inline buttons.

## Database and Migrations

SQLite is used by default — the file is at `data/bot.sqlite3`. PostgreSQL is recommended for production:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/velvet
```

Apply migrations:

```bash
alembic upgrade head
```

Create a new revision after editing models:

```bash
alembic revision --autogenerate -m "add column foo"
alembic upgrade head
```

On first run, the bot creates tables automatically if they don't exist (`Base.metadata.create_all`). In production it's better to run `alembic upgrade head` explicitly and remove `create_tables=True` from `app.py` if you want strict schema control.

## Testing and Code Style

```bash
make dev         # install with dev extras
make test        # pytest + coverage
make lint        # ruff + mypy
make format      # auto-format + auto-fix
```

Unit tests cover:

- Settings loading and validation (including duplicate plan ID protection)
- Repositories (create / extend / expire subscription, payment aggregates)
- Subscription service (idempotent activation, extension, expired reconciliation)
- Crypto Pay webhook HMAC signature
- ThrottlingMiddleware (anti-flood, purchase quota, admin bypass)

### Live Price Editing

Open `/admin` → **💰 Pricing** → select a plan → send the new price as a message
(`7.50`, `12`, `0.5` — dot or comma, no currency symbol). To revert to the `.env` value,
tap **↩️ Reset to Default**. Overrides are stored in the `price_overrides` table;
already-paid subscriptions and active invoices keep their original amount.

## Deployment

> Full guide (DNS, HTTPS, systemd, Docker, backups, updates) is in [DEPLOY.md](DEPLOY.md). Quick summary below.

### systemd

```ini
# /etc/systemd/system/velvet-bot.service
[Unit]
Description=Velvet Telegram Bot
After=network-online.target

[Service]
User=bot
WorkingDirectory=/opt/velvet-bot
EnvironmentFile=/opt/velvet-bot/.env
ExecStart=/opt/velvet-bot/.venv/bin/python -m bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now velvet-bot
```

### Docker

`docker compose up -d --build` — build and start. The `./data` volume persists the SQLite database across restarts.

### Reverse Proxy for Webhook

Minimal nginx fragment:

```nginx
location /cryptopay {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## FAQ and Troubleshooting

**The bot can't generate an invite link.**
Make sure the bot is a channel administrator with the **"Invite users via link"** permission,
and that `CHANNEL_ID` is correct (negative number, format `-100…`).

**Payment went through but the subscription isn't activated.**
If webhook is disabled — wait up to `POLL_INTERVAL_SECONDS` seconds or tap "Check Payment".
If using a webhook — check the logs for `cryptobot.webhook.bad_signature`
(means the token in the bot and in CryptoBot don't match).

**I want different prices for USDT and TON.**
Override `SubscriptionService._amount_for` in `src/bot/services/subscription.py` — that's the only place where the amount is resolved per currency.

**Can I run multiple bots on one Crypto Pay account?**
Yes, but each bot needs its own Crypto Pay App with a separate token — webhooks are bound to the app, not the account.

**Where are secrets stored in Docker?**
Compose reads `.env` from the project root. In Kubernetes, use a `Secret` resource and mount it as environment variables.

## License

MIT — see [LICENSE](LICENSE).
