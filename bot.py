import json
import os
from pathlib import Path
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TESTS_FILE = DATA_DIR / "tests.json"
USERS_DIR = DATA_DIR / "users"

DATA_DIR.mkdir(exist_ok=True)
USERS_DIR.mkdir(exist_ok=True)


DEFAULT_BOT_TOKEN = "8262194580:AAEAKd_DaRlSdrX42uwL6Zdj6Xl5PSA7JK8"
DEFAULT_ADMIN_ID = "8058345468"


ADMIN_MENU, ADMIN_COUNT, ADMIN_QUESTION, ADMIN_OPTION_A, ADMIN_OPTION_B, ADMIN_OPTION_C, ADMIN_OPTION_D, ADMIN_CORRECT = range(8)


def load_tests():
    if not TESTS_FILE.exists():
        return []
    with open(TESTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tests(tests):
    with open(TESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)


def user_progress_path(user_id: int) -> Path:
    return USERS_DIR / f"{user_id}.json"


def save_user_progress(user_id: int, progress: dict):
    p = user_progress_path(user_id)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def load_user_progress(user_id: int) -> dict | None:
    p = user_progress_path(user_id)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_options_block(text: str) -> tuple[dict, str] | None:
    """Parse a block of text with four lines starting `a)`, `b)`, `c)`, `d)`.
    The correct option should have parentheses around its text, e.g. c) (29).
    Returns (options_dict, correct_key) or None on failure.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) < 4:
        return None
    opts = {}
    correct = None
    for ln in lines[:4]:
        if len(ln) < 2 or ln[1] != ")":
            return None
        key = ln[0].lower()
        rest = ln[2:].strip()
        
        if "(" in rest and ")" in rest:
          
            inner = rest[rest.find("(") + 1 : rest.rfind(")")].strip()
    
            opts[key] = rest.replace("(", "").replace(")", "").strip()
            correct = key
        else:
            opts[key] = rest
    if set(opts.keys()) >= {"a", "b", "c", "d"} and correct in opts:
        return opts, correct
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tests = load_tests()
    if not tests:
        await update.message.reply_text("Hozircha testlar yo'q. Admin tomonidan testlar kiritilishini kuting.")
        return
    user_id = update.effective_user.id
    
    progress = {"index": 0, "correct": 0, "incorrect": 0}
    save_user_progress(user_id, progress)
    await send_question(update, context, user_id, progress)


async def send_question(update_or_query, context: ContextTypes.DEFAULT_TYPE, user_id: int, progress: dict):
    tests = load_tests()
    idx = progress["index"]
    if idx >= len(tests):
    
        text = f"Test tugadi. To'g'ri: {progress['correct']}, Noto'g'ri: {progress['incorrect']}"
    
        if hasattr(update_or_query, "answer"):
            await update_or_query.message.reply_text(text)
        else:
            await update_or_query.message.reply_text(text)
    
        p = user_progress_path(user_id)
        if p.exists():
            p.unlink()
        return

    q = tests[idx]
    
    keyboard = []
    for key in ["a", "b", "c", "d"]:
        label = f"{key}) {q['options'][key]}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"answer|{idx}|{key}")])
    text = f"Savol {idx+1}: {q['question']}"

    if hasattr(update_or_query, "message"):
        await update_or_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
    
        await update_or_query.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("answer|"):
        _, idx_s, chosen = data.split("|")
        idx = int(idx_s)
        tests = load_tests()
        if idx >= len(tests):
            await query.message.reply_text("Bu savol topilmadi.")
            return
        test = tests[idx]
        correct = test["correct"]
        user_id = query.from_user.id
        progress = load_user_progress(user_id) or {"index": 0, "correct": 0, "incorrect": 0}
    
        if progress["index"] != idx:
            await query.message.reply_text("Bu savolga javob bera olmaysiz (yoki allaqachon o'tib ketilgan).")
            return
        if chosen == correct:
            progress["correct"] += 1
            await query.message.reply_text("To'g'ri ✅")
        else:
            progress["incorrect"] += 1
    
            await query.message.reply_text(f"Noto'g'ri ❌. to'g'ri javob: {correct}")
        progress["index"] += 1
        save_user_progress(user_id, progress)
    
        await send_question(query, context, user_id, progress)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    admin_id = os.getenv("ADMIN_ID", DEFAULT_ADMIN_ID)
    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("Siz admin emassiz.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton("Create Tests", callback_data="admin_create")],
        [InlineKeyboardButton("Delete All Tests", callback_data="admin_delete_all")],
        [InlineKeyboardButton("Cancel", callback_data="admin_cancel")],
    ]
    await update.message.reply_text("Admin menyu:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_MENU


async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "admin_create":
        await query.message.reply_text("nechta test kiritmoqchisiz ?:")
        return ADMIN_COUNT
    if data == "admin_delete_all":
        save_tests([])
        await query.message.reply_text("Barcha testlar o'chirildi.")
        return ConversationHandler.END
    await query.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END


async def admin_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        n = int(text)
        if n <= 0:
            n = 30
    except Exception:
        n = 30
    context.user_data["admin_target"] = n
    context.user_data["admin_index"] = 0
    context.user_data["admin_tests"] = []
    await update.message.reply_text(f"Savol 1 ni kiriting (umumiy testlar soni: {n}):")
    return ADMIN_QUESTION


async def admin_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data.setdefault("admin_tests", [])
    context.user_data.setdefault("admin_index", 0)
    context.user_data["current_question"] = text
    context.user_data["current_options"] = {}
    await update.message.reply_text("a) variantni kiriting:")
    return ADMIN_OPTION_A


async def admin_option_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["current_options"]["a"] = text
    await update.message.reply_text("b) variantni kiriting:")
    return ADMIN_OPTION_B

async def admin_option_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["current_options"]["b"] = text
    await update.message.reply_text("c) variantni kiriting:")
    return ADMIN_OPTION_C

async def admin_option_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["current_options"]["c"] = text
    await update.message.reply_text("d) variantni kiriting:")
    return ADMIN_OPTION_D

async def admin_option_d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["current_options"]["d"] = text

    await update.message.reply_text("To'g'ri variantni kiriting (a/b/c/d):")
    return ADMIN_CORRECT


async def admin_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in {"a", "b", "c", "d"}:
        await update.message.reply_text("iltimos faqat a, b, c, d kabi variyantlardan foydalaning.")
        return ADMIN_CORRECT

    context.user_data["correct_answer"] = text
    
    qtext = context.user_data.get("current_question")
    options = context.user_data["current_options"]
    correct = context.user_data.get("correct_answer")

    context.user_data.setdefault("admin_tests", []).append({"question": qtext, "options": options, "correct": correct})
    context.user_data["admin_index"] += 1
    idx = context.user_data["admin_index"]
    target = context.user_data["admin_target"]

    if idx >= target:
    
        tests = load_tests()
        tests.extend(context.user_data["admin_tests"])
        save_tests(tests)
        await update.message.reply_text(f"{target} ta savol muvaffaqiyatli saqlandi.")
        return ConversationHandler.END
    else:
        await update.message.reply_text(f"Savol {idx+1} ni kiriting (umumiy test soni: {target}):")
        return ADMIN_QUESTION


async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin operatsiyasi bekor qilindi.")
    return ConversationHandler.END


def main():
    token = os.getenv("BOT_TOKEN", DEFAULT_BOT_TOKEN)
    if not token:
        print("BOT token not set (and no default provided). Set BOT_TOKEN env var.")
        return
    app = ApplicationBuilder().token(token).build()

    # user handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback, pattern=r"^answer\|"))

    # admin conversation
    conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_command)],
        states={
            ADMIN_MENU: [CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_")],
            ADMIN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_count)],
            ADMIN_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_question)],
            ADMIN_OPTION_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_option_a)],
            ADMIN_OPTION_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_option_b)],
            ADMIN_OPTION_C: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_option_c)],
            ADMIN_OPTION_D: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_option_d)],
            ADMIN_CORRECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_correct)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin)],
        per_user=True,
    )
    app.add_handler(conv)

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
