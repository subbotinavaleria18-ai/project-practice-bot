#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram-бот "StudyBot" — помощник для студентов
"""

import asyncio
import sqlite3
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======================= КОНФИГУРАЦИЯ =======================

TOKEN = 8688176370:AAF7tB9zRxx7M9jxvtYaE1OBLF3BRtIUvUc

# ======================= БАЗА ДАННЫХ =======================
def init_db():
    conn = sqlite3.connect("studybot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        question TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def save_question(user_id, username, question):
    conn = sqlite3.connect("studybot.db")
    c = conn.cursor()
    c.execute("INSERT INTO questions (user_id, username, question, created_at) VALUES (?, ?, ?, ?)",
              (user_id, username, question, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ======================= КОМАНДЫ БОТА =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я StudyBot — помощник для студентов.\n\n"
        "/help — список команд\n"
        "/lab — материалы по лабораторным работам\n"
        "/ask <текст> — задать вопрос\n"
        "/remind <часы> <текст> — напомнить\n"
        "/quiz — викторина по IT\n"
        "📸 Отправь фото — я отвечу!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Команды:\n"
        "/start — начать\n"
        "/help — эта справка\n"
        "/lab — список лабораторных\n"
        "/ask Вопрос? — сохранить вопрос\n"
        "/remind 2 Сдать отчёт — напомнить через 2 часа\n"
        "/quiz — викторина (5 вопросов)"
    )

async def lab_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Лабораторная 1", callback_data='lab1')],
        [InlineKeyboardButton("Лабораторная 2", callback_data='lab2')],
        [InlineKeyboardButton("Лабораторная 3", callback_data='lab3')],
    ]
    await update.message.reply_text("Выберите лабораторную:", reply_markup=InlineKeyboardMarkup(keyboard))

async def lab_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    texts = {
        'lab1': "Лаб 1: Виртуальные машины. Установите VirtualBox и Ubuntu.",
        'lab2': "Лаб 2: Командная строка Linux. Изучите команды cd, ls, chmod.",
        'lab3': "Лаб 3: Git. Создайте репозиторий и сделайте pull request.",
    }
    await query.edit_message_text(texts.get(query.data, "Неизвестная лабораторная"))

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Напишите вопрос после /ask, например: /ask Как установить Python?")
        return
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    save_question(user_id, username, question)
    await update.message.reply_text("✅ Ваш вопрос сохранён! Ответ появится позже.")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /remind <часы> <текст>\nПример: /remind 1 Сдать работу")
        return
    try:
        hours = float(context.args[0])
        text = ' '.join(context.args[1:])
        await update.message.reply_text(f"⏰ Напомню через {hours} час(а): {text}")
        asyncio.create_task(send_reminder(update.effective_user.id, text, hours, context.bot))
    except ValueError:
        await update.message.reply_text("Ошибка: часы должны быть числом")

async def send_reminder(user_id, text, hours, bot):
    await asyncio.sleep(hours * 3600)
    await bot.send_message(chat_id=user_id, text=f"🔔 НАПОМИНАНИЕ\n{text}")

# ======================= ВИКТОРИНА =======================
QUIZ = [
    {"q": "Что означает HTML?", "a": "Hyper Text Markup Language"},
    {"q": "Какой командой создаётся новая ветка в Git?", "a": "git checkout -b"},
    {"q": "Какой тег для ссылки в HTML?", "a": "<a>"},
]

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quiz_index'] = 0
    context.user_data['quiz_score'] = 0
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get('quiz_index', 0)
    if idx >= len(QUIZ):
        score = context.user_data.get('quiz_score', 0)
        await update.message.reply_text(f"🎉 Викторина окончена! Результат: {score}/{len(QUIZ)}")
        return
    q = QUIZ[idx]
    await update.message.reply_text(f"❓ Вопрос {idx+1}: {q['q']}\n\nНапишите ответ текстом")

async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get('quiz_index', 0)
    if idx >= len(QUIZ):
        return
    correct = QUIZ[idx]['a'].lower()
    user_answer = update.message.text.lower()
    if user_answer == correct:
        context.user_data['quiz_score'] = context.user_data.get('quiz_score', 0) + 1
        await update.message.reply_text("✅ Правильно!")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильный ответ: {correct}")
    context.user_data['quiz_index'] = idx + 1
    await ask_question(update, context)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo=update.message.photo[-1].file_id,
        caption="📸 Получил ваше фото! Спасибо, очень креативно!"
    )

# ======================= ЗАПУСК =======================
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lab", lab_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("quiz", quiz_start))
    app.add_handler(CallbackQueryHandler(lab_callback, pattern='^lab'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_answer))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    print("Бот StudyBot запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
