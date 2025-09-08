from datetime import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.helpers import mention_html
import unicodedata
import re

from shivu import user_collection, collection, application

# -----------------------
# Game State
# -----------------------
active_guesses = {}  # chat_id -> {...}
user_streaks = {}    # user_id -> streak
user_correct_counts = {}  # user_id -> total correct (for waifu bonus)

# -----------------------
# Support group / channel
# -----------------------
SUPPORT_GROUP_ID = -1002346084159
SUPPORT_GROUP_URL = "https://t.me/The_Moon_Network"

# -----------------------
# Rarity mapping
# -----------------------
RARITY_MAP = {
    1: "🟢 Common",
    2: "🔵 Medium",
    3: "🟠 Rare",
    4: "🟡 Legendary",
    5: "🪽 Celestial",
    6: "💮 Exclusive",
    7: "🎐 Special",
    8: "🔮 Limited"
}

# -----------------------
# Aliases (exact matches only)
# -----------------------
ALIASES = {
    "rimuru tempest": ["rimuru"],
    # "monkey d luffy": ["luffy"],
}

# -----------------------
# Normalization + tokenization
# -----------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)   # keep only letters, digits, spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def tokenize(text: str):
    return normalize_text(text).split()

# -----------------------
# Exact-only correctness (full name or any whole-word)
# -----------------------
def is_guess_correct(user_guess: str, correct_answer: str) -> bool:
    ug_norm = normalize_text(user_guess)
    ca_norm = normalize_text(correct_answer)

    # Full name exact match
    if ug_norm == ca_norm:
        return True

    # Any whole word exact match (first/last/middle)
    ug_tokens = set(tokenize(user_guess))
    ca_tokens = set(tokenize(correct_answer))
    if ug_tokens & ca_tokens:
        return True

    # Alias exact match
    alias_list = ALIASES.get(correct_answer.lower(), [])
    for alias in alias_list:
        if ug_norm == normalize_text(alias) or (ug_tokens & set(tokenize(alias))):
            return True

    return False

# -----------------------
# Hint masking
# -----------------------
def masked_answer(answer: str, reveal_n: int) -> str:
    """
    Reveal first N alphanumeric characters across the whole answer (spaces/punct stay same).
    E.g., "Naruto Uzumaki" with N=1 -> "N***** *******"
          N=2 -> "Na**** ******"
    """
    shown = 0
    out = []
    for ch in answer:
        if ch.isalnum():
            if shown < reveal_n:
                out.append(ch)
                shown += 1
            else:
                out.append('*')
        else:
            out.append(ch)
    return ''.join(out)

# -----------------------
# Must-join check
# -----------------------
async def is_user_in_support_group(context: CallbackContext, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(SUPPORT_GROUP_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# -----------------------
# Fetch a random character from DB
# -----------------------
async def get_random_character():
    try:
        pipeline = [{'$sample': {'size': 1}}]
        characters = await collection.aggregate(pipeline).to_list(length=1)
        return characters[0] if characters else None
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return None

# -----------------------
# Start a new anime guessing game
# -----------------------
async def start_anime_guess_cmd(update: Update, context: CallbackContext):
    current_time = datetime.now()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_mention = mention_html(user_id, update.effective_user.first_name)

    # Must join support group check
    joined = await is_user_in_support_group(context, user_id)
    if not joined:
        keyboard = [[InlineKeyboardButton("Join Support channel", url=SUPPORT_GROUP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ {user_mention}, Join the support channel, then use /nguess !",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    # If a game is already running, end it and start a new one
    if chat_id in active_guesses and active_guesses[chat_id].get('active', False):
        del active_guesses[chat_id]
        await update.message.reply_text(
            f"♻️ {user_mention} started a new game, replacing the previous one!",
            parse_mode=ParseMode.HTML
        )

    correct_character = await get_random_character()
    if not correct_character:
        await update.message.reply_text(
            "⚠️ No characters found. Give it another shot later.",
            parse_mode=ParseMode.HTML
        )
        return

    question = (
        "🌸 Any idea who this is? 🌸\n"
        "Type the name below. Use /hint if you need help (max 2)."
    )

    sent_message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],
        caption=question,
        parse_mode=ParseMode.HTML
    )

    # Generate a jump link for the message (supergroups only)
    if str(chat_id).startswith("-100"):
        message_link = f"https://t.me/c/{str(chat_id)[4:]}/{sent_message.message_id}"
    else:
        message_link = None

    active_guesses[chat_id] = {
        'correct_answer': correct_character['name'],
        'start_time': current_time,
        'last_guess_time': current_time,   # 30s activity window
        'attempts': 0,
        'active': True,
        'character_data': correct_character,
        'message_link': message_link,
        'starter_id': user_id,
        'last_player_id': None,
        'hints_used': 0  # max 2 per round (anyone can trigger)
    }

    # Start 30-second timeout task
    asyncio.create_task(guess_timeout(context, chat_id))

# -----------------------
# Timeout function (30s per guess only)
# -----------------------
async def guess_timeout(context: CallbackContext, chat_id: int):
    while chat_id in active_guesses:
        guess_data = active_guesses[chat_id]
        now = datetime.now()

        elapsed = (now - guess_data['last_guess_time']).total_seconds()
        wait_time = max(30 - elapsed, 0)
        await asyncio.sleep(wait_time)

        # No new guess during the 30s window
        if chat_id in active_guesses and active_guesses[chat_id]['last_guess_time'] == guess_data['last_guess_time']:
            correct_answer = active_guesses[chat_id]['correct_answer']

            # Reset only one player's streak: last guesser else starter
            target_id = guess_data.get('last_player_id') or guess_data.get('starter_id')
            if target_id and target_id in user_streaks:
                user_streaks[target_id] = 0

            del active_guesses[chat_id]

            mention = f"<a href='tg://user?id={target_id}'>this player</a>" if target_id else "the player"
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⌛ Time’s over — The correct name {correct_answer}."
                    f"\n🔥 Streak has been reset for {mention}."
                    f"\nUse /nguess to start a new game."
                ),
                parse_mode=ParseMode.HTML
            )
            return  # stop loop; users must /nguess again

# -----------------------
# Handle user guesses
# -----------------------
async def guess_text_handler(update: Update, context: CallbackContext):
    if update.message is None:
        return

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    user_name = update.message.from_user.first_name or "Player"
    user_mention = mention_html(user_id, user_name)

    if chat_id not in active_guesses:
        return

    correct_data = active_guesses[chat_id]
    correct_answer = correct_data['correct_answer']

    # Track last guesser and reset 30s timer
    correct_data['last_player_id'] = user_id
    correct_data['last_guess_time'] = datetime.now()

    # Check correctness
    correct = is_guess_correct(user_answer, correct_answer)
    correct_data['attempts'] += 1
    attempts = correct_data['attempts']

    if correct:
        # Streaks
        streak = user_streaks.get(user_id, 0) + 1
        user_streaks[user_id] = streak

        # Mora reward (based on streak)
        mora_earned = 20000 + (streak * 10000)
        await user_collection.update_one(
            {'id': user_id},
            {
                '$inc': {'balance': mora_earned},
                '$set': {'name': user_name}  # keep display name fresh
            },
            upsert=True
        )

        # Correct count (for waifu bonus)
        correct_count = user_correct_counts.get(user_id, 0) + 1
        user_correct_counts[user_id] = correct_count

        # Score (leaderboard)
        chat_key = f"guess_wins_by_chat.{chat_id}"
        await user_collection.update_one(
            {'id': user_id},
            {
                '$inc': {
                    'guess_wins': 1,        # global
                    chat_key: 1             # per chat
                },
                '$set': {'name': user_name}
            },
            upsert=True
        )

        # Waifu bonus every 10 correct (uses current character)
        waifu_bonus = ""
        waifu_data = correct_data['character_data']
        if correct_count % 10 == 0:
            rarity_label = RARITY_MAP.get(waifu_data.get('rarity', 0), "❔ Unknown")
            waifu_bonus = f"\n💖 <b>You’ve unlocked a special waifu: {rarity_label} {waifu_data['name']}!</b>"
            await user_collection.update_one(
                {'id': user_id},
                {'$addToSet': {'waifus': {
                    "name": waifu_data['name'],
                    "img": waifu_data['img_url'],
                    "rarity": rarity_label
                }}},
                upsert=True
            )

        # Badges
        badges = await award_badges(user_id, streak)

        await update.message.reply_text(
            f"🎉 {user_mention} Guessed in {attempts} Attempts!\n\n"
            f"🔑 Answer: {correct_answer}\n"
            f"💰 Earned: 〄 {mora_earned} Mora!\n"
            f"🔥 Streak: {streak}{badges}{waifu_bonus}",
            parse_mode=ParseMode.HTML
        )

        # End round and auto-start next one
        del active_guesses[chat_id]
        await asyncio.sleep(2)
        await start_anime_guess_cmd(update, context)

    else:
        # Only starter gets the "keep trying" encouragement
        if user_id == correct_data['starter_id']:
            message_link = correct_data.get('message_link', None)
            feedback = "💪 Don't give up!" if attempts < 3 else "🙌 So close!"
            keyboard = [[InlineKeyboardButton("🔍 Where is character", url=message_link)]] if message_link else None
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

            await update.message.reply_text(
                f"{feedback} {user_mention}, Find the character and try again!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

# -----------------------
# /hint (anyone can use; max 2 per round total)
# -----------------------
async def hint_cmd(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in active_guesses or not active_guesses[chat_id].get('active'):
        await update.message.reply_text("❌ No active game. Use /nguess to start one.")
        return

    data = active_guesses[chat_id]
    used = data.get('hints_used', 0)
    if used >= 2:
        await update.message.reply_text("🧩 Hints exhausted for this round (max 2).")
        return

    # Increase hint count and generate masked string
    used += 1
    data['hints_used'] = used
    answer = data['correct_answer']
    masked = masked_answer(answer, reveal_n=used)  # reveal 1 then 2 alnum chars

    # Reset the 30s timer since there's activity
    data['last_guess_time'] = datetime.now()

    await update.message.reply_text(
        f"🧠 <b>Hint #{used}:</b> <code>{masked}</code>",
        parse_mode=ParseMode.HTML
    )

# -----------------------
# /guessboard (leaderboard)
# -----------------------
async def guessboard_cmd(update: Update, context: CallbackContext):
    # Global top 10
    pipeline_global = [
        {'$match': {'guess_wins': {'$gt': 0}}},
        {'$project': {
            'id': 1,
            'name': {'$ifNull': ['$name', 'Player']},
            'score': '$guess_wins'
        }},
        {'$sort': {'score': -1}},
        {'$limit': 10}
    ]

    try:
        top_global = await user_collection.aggregate(pipeline_global).to_list(length=10)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Guessboard error: {e}")
        return

    if not top_global:
        await update.message.reply_text(
            "📊 <b>Guessboard</b>\nNo scores yet. Be the first to guess right!",
            parse_mode='HTML'
        )
        return

    # Build leaderboard message
    lines = ["🌐 <b>Global Guessboard</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, doc in enumerate(top_global, start=1):
        icon = medals[i-1] if i <= 3 else f"{i}."
        uid = doc.get('id')
        score = doc.get('score', 0)
        name = doc.get('name', 'Player')
        lines.append(f"{icon} {mention_html(uid, name)} — <b>{score}</b> correct")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    
# -----------------------
# Badge awarding
# -----------------------
async def award_badges(user_id, streak):
    if streak == 5:
        return "\n🏅 Bronze Badge Earned!"
    elif streak == 10:
        return "\n🥈 Silver Badge Earned!"
    elif streak == 20:
        return "\n🥇 Gold Badge Earned!"
    return ""
