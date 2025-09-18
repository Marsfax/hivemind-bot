import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневный отчет о активности в канале"""
    # Здесь будет код для сбора статистики и генерации отчета
    report_text = "📊 Ежедневный отчет о активности в канале:\n\n"
    report_text += "• Всего комментариев за день: 15\n"
    report_text += "• Удалено нарушающих правил: 3\n"
    report_text += "• Популярные темы: технологии, наука\n"
    report_text += "• Настроение аудитории: позитивное\n\n"
    report_text += "💡 Рекомендации: продолжать обсуждать технологические новости"
    
    # Отправляем отчет создателю бота
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=report_text)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
    🤖 Привет! Я HiveMind — твой AI-помощник для управления Telegram-каналом.

    Я могу:
    • Анализировать комментарии на токсичность
    • Предлагать идеи для контента
    • Помогать с модерацией

    Добавь меня в свой канал как администратора, и я начну работу!
    """
    await update.message.reply_text(welcome_text)

async def analyze_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ комментария с помощью DeepSeek"""
    comment_text = update.message.text
    
    # Подготовка запроса к DeepSeek API
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Ты — AI-модератор. Проанализируй комментарий на предмет токсичности, спама или нарушений. Ответь кратко, в формате: 'Токсичность: X/10. Вердикт: [ОДОБРИТЬ/ПРЕДУПРЕДИТЬ/УДАЛИТЬ]'"
            },
            {
                "role": "user",
                "content": f"Проанализируй этот комментарий: '{comment_text}'"
            }
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        result = response.json()
        
        ai_response = result['choices'][0]['message']['content']
        await update.message.reply_text(f"🔍 Результат анализа:\n\n{ai_response}")
        
    except Exception as e:
        logging.error(f"Ошибка при запросе к DeepSeek: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при анализе. Попробуйте позже.")

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    # Добавляем ежедневный отчет (отправляется в 18:00 каждый день)
    application.job_queue.run_daily(send_daily_report, time=datetime.time(hour=18, minute=0))
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_comment))
    
    # Запускаем бота
    application.run_polling()
    logging.info("Бот запущен!")

if __name__ == '__main__':
    main()
