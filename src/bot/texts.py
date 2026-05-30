"""All user-facing strings live here so they are easy to translate or rebrand.

English copy — translated and adapted from Russian.
Bot brand name: Velvet (see WELCOME for usage).
"""

from __future__ import annotations

from decimal import Decimal

from .config import Plan

# ── /start ──────────────────────────────────────────────────────────────────────
WELCOME = (
    "<b>Hey, {name}!</b>\n\n"
    "Welcome to <b>Velvet</b> — your gateway to exclusive subscriber-only content.\n\n"
    "Use the buttons below to get a subscription, learn more about the channel, "
    "or reach out to support."
)

BTN_BUY = "💳 Get Access"
BTN_INFO = "ℹ️ How It Works"
BTN_SUPPORT = "🆘 Support"
BTN_MY_SUBSCRIPTION = "👤 My Subscription"


# ── INFO ────────────────────────────────────────────────────────────────────────
INFO = (
    "<b>About the channel</b>\n\n"
    "Exclusive content published only for active subscribers — "
    "no public access.\n\n"
    "<b>How it works</b>\n"
    "1. Choose a plan and pay via CryptoBot — USDT or TON.\n"
    "2. Once your payment is confirmed, you'll receive a personal one-time invite link.\n"
    "3. You'll get reminders 3 days and 1 day before your subscription expires.\n"
    "4. When your subscription ends, the bot will automatically remove you from the channel.\n\n"
    "All payments are secure and processed by CryptoBot."
)


# ── Subscription menu ──────────────────────────────────────────────────────────
CHOOSE_PLAN = "<b>Choose a plan:</b>"

PLAN_BUTTON = "{title} — {price} {asset}"


def format_plan_row(plan: Plan, asset: str) -> str:
    price = _format_price(plan.price)
    return PLAN_BUTTON.format(title=plan.title, price=price, asset=asset)


CHOOSE_ASSET = (
    "Plan: <b>{title}</b>\n"
    "Duration: <b>{days} days</b>\n"
    "Price: <b>{price}</b>\n\n"
    "Select your payment currency:"
)


INVOICE_CREATED = (
    "Your invoice has been created.\n\n"
    "Plan: <b>{title}</b> ({days} days)\n"
    "Amount due: <b>{amount} {asset}</b>\n\n"
    "Pay via CryptoBot using one of the options below. Once your payment is confirmed, "
    "the bot will send you an invite link to the channel."
)

BTN_PAY_IN_BOT = "💸 Pay in CryptoBot"
BTN_PAY_MINIAPP = "🚀 Pay in Mini App"
BTN_CHECK = "🔄 Check Payment"
BTN_CANCEL = "✖️ Cancel"
BTN_BACK = "« Back"

INVOICE_NOT_PAID = "Payment not confirmed yet. Please try again in a minute."
INVOICE_EXPIRED = "This invoice has expired. Please create a new one."
INVOICE_CANCELLED = "Invoice cancelled."

PAYMENT_RECEIVED = (
    "✅ <b>Payment received!</b>\n\n"
    "Your subscription is active until <b>{until}</b>.\n\n"
    "Your personal one-time invite link:\n{link}"
)


PAYMENT_RECEIVED_EXTENDED = (
    "✅ <b>Payment received!</b>\n\n"
    "Your subscription has been extended until <b>{until}</b>. "
    "You still have full access to the channel."
)


# ── My subscription ────────────────────────────────────────────────────────────
NO_SUBSCRIPTION = (
    "You don't have an active subscription yet.\n\n"
    "Tap <b>Get Access</b> to get started."
)

ACTIVE_SUBSCRIPTION = (
    "<b>Your subscription is active</b>\n\n"
    "Valid until: <b>{until}</b>\n"
    "Days remaining: <b>{days}</b>\n\n"
    "You can renew early — any extra days will simply be added on top of your current period."
)

EXPIRED_SUBSCRIPTION = (
    "Your subscription expired on {when}. Subscribe again to regain access to the channel."
)


# ── Reminders ──────────────────────────────────────────────────────────────────
REMINDER_BEFORE = (
    "⏰ <b>Your subscription is expiring soon</b>\n\n"
    "<b>{days} days</b> left (until {until}).\n"
    "Renew now to keep your access — extra days will be added to your current period."
)

REMINDER_LAST_DAY = (
    "⚠️ <b>Your subscription expires tomorrow</b>\n\n"
    "Access to the channel will be closed on {until}. Renew today to stay in."
)

SUBSCRIPTION_ENDED = (
    "Your subscription has ended — access to the channel has been revoked.\n\n"
    "To get back in, start a new subscription using the button below."
)


# ── Admin ──────────────────────────────────────────────────────────────────────
ADMIN_MENU = (
    "<b>Admin Panel</b>\n\n"
    "Total users: <b>{users}</b>\n"
    "Active subscriptions: <b>{active}</b>\n"
    "Total payments: <b>{paid}</b>\n"
    "Revenue: <b>{revenue}</b>\n\n"
    "Subscriptions purchased in the last 30 days: <b>{recent}</b>"
)

ADMIN_FORBIDDEN = "This command is restricted to administrators."

ADMIN_BTN_REFRESH = "🔄 Refresh"
ADMIN_BTN_STATS_BY_PLAN = "📊 By Plan"
ADMIN_BTN_LIST_USERS = "👥 Recent Subs"
ADMIN_BTN_PRICING = "💰 Pricing"
ADMIN_BTN_RESET_PRICE = "↩️ Reset to Default"
ADMIN_BTN_CANCEL_EDIT = "✖️ Cancel"
ADMIN_BTN_BACK = "« Back"
ADMIN_BTN_CLOSE = "Close"

ADMIN_PRICING_HEADER = (
    "<b>Pricing</b>\n\n"
    "Tap a plan to set a new price. The ✏️ icon means the price has been overridden "
    "in the admin panel. Changes apply to new invoices only — existing subscriptions "
    "are not affected.\n"
)

ADMIN_PRICING_ENTER_NEW = (
    "<b>{title}</b>\n"
    "Duration: {days} days\n"
    "Current price: <b>{price}</b>\n"
    "Config default: <b>{default}</b>\n\n"
    "Send the new price as a message (e.g. <code>7.50</code>), or tap Cancel."
)

ADMIN_PRICING_SAVED = "✅ Price for <b>{title}</b> updated to <b>{price}</b>."
ADMIN_PRICING_RESET = "↩️ Price for <b>{title}</b> reset to default: <b>{price}</b>."
ADMIN_PRICING_BAD_INPUT = "Please enter a positive number, e.g. <code>7.50</code>."

ADMIN_STATS_BY_PLAN_HEADER = "<b>Sales by Plan</b>\n\n"
ADMIN_STATS_BY_PLAN_ROW = "• <b>{title}</b> — {count} payments totalling {revenue}\n"

ADMIN_RECENT_HEADER = "<b>Last 20 Subscriptions</b>\n\n"
ADMIN_RECENT_ROW = "• <code>{user_id}</code> — {title} until {until}\n"


# ── Errors / misc ──────────────────────────────────────────────────────────────
GENERIC_ERROR = "Something went wrong. Please try again later."
THROTTLED = "Too many requests. Please wait a moment and try again."
UNKNOWN_COMMAND = "Command not recognized. Press /start to open the menu."

INVITE_LINK_FAILED = (
    "Payment confirmed, but we couldn't generate your invite link. "
    "Please contact support — we'll grant you access manually."
)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _format_price(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01")) if value % 1 else value.quantize(Decimal("1"))
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def format_amount(value: Decimal, asset: str) -> str:
    return f"{_format_price(value)} {asset}"
