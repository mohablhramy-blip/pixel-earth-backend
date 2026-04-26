#!/usr/bin/env python3
"""
🌍 PIXEL EARTH BOT 🌍
Draw the World. Own the World.
Official Telegram Bot - Pixel Earth Platform
Version: 1.0.0
Author: [YOUR NAME]
License: MIT
"""

import logging
import json
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    BotCommand, LabeledPrice, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

from config import *
from database import *

load_dotenv()

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== BRANDING ====================
APP_NAME = "Pixel Earth"
APP_URL = os.getenv("FRONTEND_URL", "https://pixel-earth.netlify.app")
SUPPORT_USERNAME = "@PixelEarthSupport"

# ==================== UI TEMPLATES ====================

LOGO = """
🌍 <b>PIXEL EARTH</b> 🌍
"""

TAGLINE = """
<i>Draw the World. Own the World.</i>
"""

DIVIDER = """
━━━━━━━━━━━━━━━━━━━━━
"""

WELCOME_MESSAGE = f"""
{LOGO}
{TAGLINE}
{DIVIDER}

🎨 <b>THE FIRST GLOBAL CANVAS ON TELEGRAM</b>

🖌️ Draw anywhere on the real world map
💰 Pay only for what you draw — <b>1 Pixel = 1 ⭐</b>
🏆 Compete on the global leaderboard
🌐 Claim territory for your nation

{DIVIDER}

👛 <b>Your Balance:</b> {{balance}} ⭐
🖼️ <b>Pixels Owned:</b> {{pixels_owned}}
🔥 <b>Active Drawers Online:</b> {{online_count}}

{DIVIDER}

Ready to leave your mark on Earth?
"""

HELP_MESSAGE = f"""
{LOGO}
{DIVIDER}
<b>ℹ️  HOW TO PLAY</b>
{DIVIDER}

<b>🎨 DRAWING:</b>
• Tap <b>"Open Map"</b> below
• Navigate to any location on Earth
• Select a color from the palette
• Tap anywhere to draw a pixel

<b>💰 PAYMENT:</b>
• <b>1 Pixel = 1 Telegram Star (⭐)</b>
• Draw as much as you want
• When done, tap <b>"Finish"</b>
• Review your invoice
• <b>Pay</b> to claim — or <b>Cancel</b> to free pixels

<b>🏆 COMPETITION:</b>
• Claim famous landmarks
• Draw your country's flag
• Create massive pixel art
• Dominate the leaderboard

{DIVIDER}
<b>💡 PRO TIPS:</b>
• Zoom in for detailed art
• Coordinate with friends to claim large areas
• The first to claim a landmark owns it forever

{DIVIDER}
<b>📞 Support:</b> {SUPPORT_USERNAME}
<b>🌐 Website:</b> pixel-earth.app

© 2024 Pixel Earth. All rights reserved.
"""

WALLET_MESSAGE = f"""
{LOGO}
{DIVIDER}
<b>👛 MY WALLET</b>
{DIVIDER}

💰 <b>Balance:</b> {{balance}} ⭐
🖼️ <b>Pixels Owned:</b> {{pixels_owned}}
💸 <b>Total Spent:</b> {{total_spent}} ⭐
📊 <b>Account Created:</b> {{created_at}}

{DIVIDER}

<b>💎 TOP UP YOUR BALANCE:</b>
"""

LEADERBOARD_HEADER = f"""
{LOGO}
{DIVIDER}
<b>🏆 GLOBAL LEADERBOARD</b>
{DIVIDER}

The top pixel owners on Earth. 
Do you have what it takes to make the list?

"""

MY_PIXELS_HEADER = f"""
{LOGO}
{DIVIDER}
<b>🖼️ MY PIXEL COLLECTION</b>
{DIVIDER}
"""

INVOICE_MESSAGE = """
🧾 <b>YOUR INVOICE</b>
━━━━━━━━━━━━━━━━━━━━━
📊 <b>Pixels Drawn:</b> {pixel_count}
💰 <b>Price per Pixel:</b> 1 ⭐
💎 <b>TOTAL DUE:</b> {total_cost} ⭐
━━━━━━━━━━━━━━━━━━━━━
⏱️ <b>Session expires in:</b> {time_remaining}

Choose an action below:
"""

PAYMENT_SUCCESS_MESSAGE = f"""
{LOGO}
{DIVIDER}
✅ <b>PAYMENT SUCCESSFUL!</b>
{DIVIDER}

🖼️ <b>Pixels Claimed:</b> {{pixel_count}}
💸 <b>Total Paid:</b> {{total_cost}} ⭐
💰 <b>Remaining Balance:</b> {{balance}} ⭐

{DIVIDER}
🎉 Your pixels are now <b>PERMANENTLY</b> on the map!
🌍 They are visible to everyone, forever.

View them anytime with /mypixels
"""

SESSION_CANCELLED_MESSAGE = f"""
{LOGO}
{DIVIDER}
❌ <b>DRAWING CANCELLED</b>
{DIVIDER}

🆓 All {{pixel_count}} pixels have been freed.
💰 No charges were made.

{DIVIDER}
Want to try again? The map is still waiting! 🌍
"""

# ==================== KEYBOARDS ====================

def main_menu_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🌍 OPEN MAP — Start Drawing!", 
                web_app=WebAppInfo(url=APP_URL)
            )
        ],
        [
            InlineKeyboardButton("👛 My Wallet", callback_data="wallet"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("🖼️ My Pixels", callback_data="my_pixels"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ],
        [
            InlineKeyboardButton("📢 Share Pixel Earth", switch_inline_query="🌍 Draw on the real world map! Join Pixel Earth now!")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_button() -> InlineKeyboardMarkup:
    """Simple back button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main")]
    ])


def open_map_button() -> InlineKeyboardMarkup:
    """Open map button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Open Map", web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main")]
    ])


def payment_keyboard(session_id: str, total_cost: int) -> InlineKeyboardMarkup:
    """Invoice payment keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ PAY {total_cost} ⭐ — Claim Pixels", callback_data=f"pay_{session_id}")],
        [InlineKeyboardButton("❌ CANCEL — Free Pixels", callback_data=f"cancel_{session_id}")],
    ])


def topup_keyboard() -> InlineKeyboardMarkup:
    """Top up keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 50 Stars — $0.99", callback_data="topup_50")],
        [InlineKeyboardButton("⭐ 150 Stars — $2.99", callback_data="topup_150")],
        [InlineKeyboardButton("⭐ 500 Stars — $4.99 ⭐BEST VALUE", callback_data="topup_500")],
        [InlineKeyboardButton("⭐ 1000 Stars — $9.99", callback_data="topup_1000")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main")]
    ])


# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    user_id = str(user.id)
    
    # Create user account with welcome bonus
    user_data = create_user(user_id, user.username, user.first_name)
    
    # Count active users (simplified)
    online_count = 42  # You can integrate WebSocket tracking later
    
    welcome_text = WELCOME_MESSAGE.format(
        balance=user_data["stars_balance"],
        pixels_owned=user_data.get("total_pixels_owned", 0),
        online_count=online_count
    )
    
    await update.message.reply_html(
        welcome_text,
        reply_markup=main_menu_keyboard(user_id)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_html(
        HELP_MESSAGE,
        reply_markup=open_map_button()
    )


async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /map command - opens the drawing canvas."""
    await update.message.reply_html(
        f"{LOGO}\n\n🎨 Tap below to open the world map and start drawing!\n\n{DIVIDER}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌍 OPEN MAP — Draw Now!", web_app=WebAppInfo(url=APP_URL))]
        ])
    )


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wallet command."""
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_html("Please use /start first.")
        return
    
    created_at = user.get("created_at", "Unknown")
    if created_at != "Unknown":
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_at = dt.strftime("%d %B %Y")
        except:
            pass
    
    wallet_text = WALLET_MESSAGE.format(
        balance=user["stars_balance"],
        pixels_owned=user.get("total_pixels_owned", 0),
        total_spent=user.get("total_spent", 0),
        created_at=created_at
    )
    
    await update.message.reply_html(
        wallet_text,
        reply_markup=topup_keyboard()
    )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command."""
    leaders = get_leaderboard(20)
    
    leaderboard_text = LEADERBOARD_HEADER
    
    medals = ["🥇", "🥈", "🥉"]
    
    if not leaders:
        leaderboard_text += "\n😔 No one has claimed any pixels yet!\n\nBe the first! 🚀\n"
    else:
        for i, leader in enumerate(leaders):
            medal = medals[i] if i < 3 else f"  {i+1}."
            username = leader.get("username", "unknown")
            pixels = leader.get("total_pixels_owned", 0)
            
            # Highlight top 3
            if i < 3:
                leaderboard_text += f"\n{medal} <b>@{username}</b> — {pixels} pixels"
            else:
                leaderboard_text += f"\n{medal} @{username} — {pixels} pixels"
    
    total_pixels = sum(l.get("total_pixels_owned", 0) for l in leaders) if leaders else 0
    leaderboard_text += f"\n\n{DIVIDER}\n🌍 <b>Total Pixels Claimed:</b> {total_pixels:,}\n"
    
    await update.message.reply_html(
        leaderboard_text,
        reply_markup=open_map_button()
    )


async def mypixels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mypixels command."""
    user_id = str(update.effective_user.id)
    pixels = get_user_pixels(user_id)
    
    mypixels_text = MY_PIXELS_HEADER
    
    if not pixels:
        mypixels_text += "\n😔 You haven't claimed any pixels yet!\n\n"
        mypixels_text += "Tap below to start drawing on the world map! 🌍\n"
    else:
        mypixels_text += f"\n📊 <b>Total Pixels:</b> {len(pixels)}\n"
        mypixels_text += f"💸 <b>Total Spent:</b> {len(pixels)} ⭐\n\n"
        mypixels_text += "<b>📍 Recently Claimed Pixels:</b>\n\n"
        
        # Show latest 10 pixels
        for pixel in pixels[-10:]:
            x = pixel.get("x", 0)
            y = pixel.get("y", 0)
            color = pixel.get("color", "#000000")
            mypixels_text += f"🟦 ({x}, {y}) — {color}\n"
    
    await update.message.reply_html(
        mypixels_text,
        reply_markup=open_map_button()
    )


async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /share command."""
    share_text = f"""
{LOGO}
{DIVIDER}
<b>📢 SHARE PIXEL EARTH</b>
{DIVIDER}

Share this with your friends and earn <b>FREE pixels!</b>

🔗 <b>Your Referral Link:</b>
https://t.me/{context.bot.username}?start=ref_{{user_id}}

<b>🏆 Referral Program:</b>
• Invite 10 friends = <b>50 ⭐ FREE</b>
• Invite 50 friends = <b>500 ⭐ FREE</b>
• Top referrer of the month = <b>10,000 ⭐</b>

{DIVIDER}

Or just forward this message! 📤
"""
    await update.message.reply_html(
        share_text.format(user_id=update.effective_user.id),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share with Friends", switch_inline_query="🌍 Draw on the real world map! Join Pixel Earth!")]
        ])
    )


# ==================== CALLBACK HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # Navigation
    if data == "main":
        await show_main_menu(query, user_id)
    
    elif data == "wallet":
        await show_wallet(query, user_id)
    
    elif data == "leaderboard":
        await show_leaderboard(query, user_id)
    
    elif data == "my_pixels":
        await show_my_pixels(query, user_id)
    
    elif data == "help":
        await query.edit_message_text(
            HELP_MESSAGE,
            reply_markup=open_map_button(),
            parse_mode=ParseMode.HTML
        )
    
    # Top up
    elif data.startswith("topup_"):
        amount = int(data.replace("topup_", ""))
        await process_topup(query, user_id, amount)
    
    # Payment for drawing session
    elif data.startswith("pay_"):
        session_id = data.replace("pay_", "")
        await process_pixel_payment(query, user_id, session_id)
    
    # Cancel drawing session
    elif data.startswith("cancel_"):
        session_id = data.replace("cancel_", "")
        await cancel_pixel_session(query, user_id, session_id)


async def show_main_menu(query, user_id: str):
    """Show the main menu."""
    user = get_user(user_id)
    welcome_text = WELCOME_MESSAGE.format(
        balance=user["stars_balance"] if user else 100,
        pixels_owned=user.get("total_pixels_owned", 0) if user else 0,
        online_count=42
    )
    await query.edit_message_text(
        welcome_text,
        reply_markup=main_menu_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )


async def show_wallet(query, user_id: str):
    """Show wallet screen."""
    user = get_user(user_id)
    if not user:
        await query.edit_message_text("Please /start first", reply_markup=back_to_menu_button())
        return
    
    wallet_text = WALLET_MESSAGE.format(
        balance=user["stars_balance"],
        pixels_owned=user.get("total_pixels_owned", 0),
        total_spent=user.get("total_spent", 0),
        created_at="Today"
    )
    await query.edit_message_text(
        wallet_text,
        reply_markup=topup_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_leaderboard(query, user_id: str):
    """Show leaderboard."""
    leaders = get_leaderboard(20)
    text = LEADERBOARD_HEADER
    
    medals = ["🥇", "🥈", "🥉"]
    
    if not leaders:
        text += "\n😔 No pixels claimed yet!\n\nBe the first to draw! 🚀"
    else:
        for i, leader in enumerate(leaders):
            medal = medals[i] if i < 3 else f"  {i+1}."
            username = leader.get("username", "unknown")
            pixels = leader.get("total_pixels_owned", 0)
            
            if i < 3:
                text += f"\n{medal} <b>@{username}</b> — {pixels:,} pixels"
            else:
                text += f"\n{medal} @{username} — {pixels:,} pixels"
    
    total = sum(l.get("total_pixels_owned", 0) for l in leaders) if leaders else 0
    text += f"\n\n{DIVIDER}\n🌍 <b>Total Claimed:</b> {total:,} pixels"
    
    await query.edit_message_text(
        text,
        reply_markup=open_map_button(),
        parse_mode=ParseMode.HTML
    )


async def show_my_pixels(query, user_id: str):
    """Show user's pixel collection."""
    pixels = get_user_pixels(user_id)
    text = MY_PIXELS_HEADER
    
    if not pixels:
        text += "\n😔 No pixels yet!\n\nStart drawing now! 🌍"
    else:
        text += f"\n📊 <b>Total:</b> {len(pixels)} pixels\n\n<b>Recent:</b>\n"
        for pixel in pixels[-5:]:
            text += f"🟦 ({pixel.get('x',0)}, {pixel.get('y',0)}) — {pixel.get('color','#000')}\n"
    
    await query.edit_message_text(
        text,
        reply_markup=open_map_button(),
        parse_mode=ParseMode.HTML
    )


# ==================== PAYMENT PROCESSING ====================

async def process_topup(query, user_id: str, amount: int):
    """Create a Telegram Stars invoice for top-up."""
    title = f"{amount} Telegram Stars"
    description = f"Top up {amount} Stars for Pixel Earth drawing"
    payload = json.dumps({"user_id": user_id, "type": "topup", "amount": amount})
    currency = "XTR"
    prices = [LabeledPrice(title, amount)]
    
    try:
        await query.message.reply_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Empty for Telegram Stars
            currency=currency,
            prices=prices,
            start_parameter="pixel_earth_topup"
        )
        await query.edit_message_text(
            "💳 Payment invoice sent!\n\nCheck the message above to complete your purchase.",
            reply_markup=back_to_menu_button()
        )
    except Exception as e:
        logger.error(f"Invoice error: {e}")
        await query.edit_message_text(
            "❌ Error creating invoice. Please try again.",
            reply_markup=back_to_menu_button()
        )


async def process_pixel_payment(query, user_id: str, session_id: str):
    """Process payment for a drawing session."""
    session = get_session(session_id)
    
    if not session:
        await query.edit_message_text(
            "❌ Session expired or not found.\n\nStart a new drawing!",
            reply_markup=open_map_button(),
            parse_mode=ParseMode.HTML
        )
        return
    
    total_cost = session["total_cost"]
    user = get_user(user_id)
    
    if not user or user["stars_balance"] < total_cost:
        needed = total_cost - (user["stars_balance"] if user else 0)
        await query.edit_message_text(
            f"❌ <b>Insufficient Balance</b>\n\n"
            f"💰 Your Balance: {user['stars_balance'] if user else 0} ⭐\n"
            f"💎 Invoice: {total_cost} ⭐\n"
            f"⚠️ You need <b>{needed} more ⭐</b>\n\n"
            f"Top up your balance first!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Top Up Now", callback_data="wallet")],
                [InlineKeyboardButton("🔙 Back", callback_data="main")]
            ]),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Deduct balance
    new_balance = update_balance(user_id, -total_cost)
    
    # Claim the pixels
    pixels_data = json.loads(session.get("pixels_data", "[]"))
    claimed = claim_pixels(user_id, pixels_data)
    
    # Record transaction
    add_transaction(user_id, "purchase", total_cost, f"Claimed {claimed} pixels")
    
    # End the session
    end_session(session_id, "completed")
    
    # Success message
    success_text = PAYMENT_SUCCESS_MESSAGE.format(
        pixel_count=claimed,
        total_cost=total_cost,
        balance=new_balance
    )
    
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌍 Draw More!", web_app=WebAppInfo(url=APP_URL))],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main")]
        ]),
        parse_mode=ParseMode.HTML
    )


async def cancel_pixel_session(query, user_id: str, session_id: str):
    """Cancel a drawing session — free the pixels."""
    session = get_session(session_id)
    pixel_count = session.get("total_cost", 0) if session else 0
    
    end_session(session_id, "cancelled")
    
    cancel_text = SESSION_CANCELLED_MESSAGE.format(pixel_count=pixel_count)
    
    await query.edit_message_text(
        cancel_text,
        reply_markup=open_map_button(),
        parse_mode=ParseMode.HTML
    )


# ==================== PAYMENT HANDLERS ====================

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pre-checkout query — must answer within 10 seconds."""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"Pre-checkout approved for user {query.from_user.id}")


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment."""
    payment = update.message.successful_payment
    user_id = str(update.effective_user.id)
    
    try:
        payload = json.loads(payment.invoice_payload)
        amount = payload.get("amount", payment.total_amount)
        payment_type = payload.get("type", "purchase")
    except:
        amount = payment.total_amount
        payment_type = "purchase"
    
    # Add stars to user balance
