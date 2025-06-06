import telebot
import config
import ya
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = config.API_TOKEN
bot = telebot.TeleBot(API_TOKEN)


def update_stats(user_id, username):
    stats_file = "stats.json"
    stats = {}

    if os.path.exists(stats_file):
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)

    user_id_str = str(user_id)
    if user_id_str not in stats:
        stats[user_id_str] = {
            "username": username or "unknown",
            "total_requests": 0,
            "last_seen": ""
        }

    stats[user_id_str]["total_requests"] += 1
    stats[user_id_str]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👋 Привет! Я ИИ-бот, который анализирует текст.\n\n"
        "Просто пришли мне текст, и я скажу:\n"
        "📌 Тему\n🧠 Суть\n😊 Настроение\n🔎 Тип текста\n\n"
        "Команды: /help, /stats"
    )


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id,
        "🛠 Возможности:\n\n"
        "• Отправь текст — я его проанализирую\n"
        "• Результат можно сохранить\n"
        "• Я веду твою статистику\n\n"
        "Команда: /stats — узнать свою активность"
    )


@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = str(message.from_user.id)
    if os.path.exists("stats.json"):
        with open("stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)

        if user_id in stats:
            user_stats = stats[user_id]
            bot.send_message(message.chat.id,
                f"📊 Статистика:\n"
                f"Пользователь: @{user_stats['username']}\n"
                f"Всего запросов: {user_stats['total_requests']}\n"
                f"Последняя активность: {user_stats['last_seen']}"
            )
            return
    bot.send_message(message.chat.id, "Ты ещё не отправлял текстов.")


@bot.message_handler(func=lambda message: True)
def analyze_text(message):
    bot.send_chat_action(message.chat.id, 'typing')

    text = message.text
    result = ya.gpt(text)

    # Сохраняем в файл
    user_file = f"history_{message.from_user.id}.txt"
    with open(user_file, "a", encoding="utf-8") as file:
        file.write(f"User: {message.from_user.username or message.from_user.id}\n")
        file.write(f"Text: {text}\n")
        file.write(f"Result:\n{result}\n")
        file.write("-" * 40 + "\n")

    # Обновляем статистику
    update_stats(message.from_user.id, message.from_user.username)

    # Создаём кнопки
    markup = get_main_markup()
    markup.add(InlineKeyboardButton("💾 Сохранено!", callback_data="saved"))

    bot.send_message(message.chat.id, result, reply_markup=markup)


# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.from_user.id)

    if call.data == "show_stats":
        if os.path.exists("stats.json"):
            with open("stats.json", "r", encoding="utf-8") as f:
                stats = json.load(f)
            if user_id in stats:
                s = stats[user_id]
                bot.answer_callback_query(call.id)
                bot.send_message(call.message.chat.id,
                    f"📊 Статистика:\n"
                    f"Пользователь: @{s['username']}\n"
                    f"Запросов: {s['total_requests']}\n"
                    f"Последняя активность: {s['last_seen']}"
                )
            else:
                bot.send_message(call.message.chat.id, "Нет данных о тебе.")

    elif call.data == "export_history":
        path = f"history_{user_id}.txt"
        if os.path.exists(path):
            bot.send_document(call.message.chat.id, open(path, "rb"))
        else:
            bot.send_message(call.message.chat.id, "История пока пуста.")
        bot.answer_callback_query(call.id)

    elif call.data == "delete_history":
        path = f"history_{user_id}.txt"
        if os.path.exists(path):
            os.remove(path)
            bot.send_message(call.message.chat.id, "🗑 История удалена.")
        else:
            bot.send_message(call.message.chat.id, "У тебя нет сохранённой истории.")
        bot.answer_callback_query(call.id)

    elif call.data == "saved":
        bot.answer_callback_query(call.id, "Анализ уже сохранён 👍")

def get_main_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats"))
    markup.add(InlineKeyboardButton("📤 Экспорт истории", callback_data="export_history"))
    markup.add(InlineKeyboardButton("🗑 Удалить историю", callback_data="delete_history"))
    return markup


bot.infinity_polling()
