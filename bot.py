import os
import logging
import sys
from dotenv import load_dotenv


# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Проверка обязательных переменных окружения
required_vars = ['BOT_TOKEN', 'DEEPSEEK_API_KEY', 'CHANNEL_ID']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    error_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
    logger.error(error_msg)
    
    # Вывод всех переменных окружения для отладки (не для продакшена)
    logger.info("Доступные переменные окружения:")
    for key, value in os.environ.items():
        logger.info(f"{key}: {value}")

# Конфигурация
BOT_TOKEN = os.getenv('8217261903:AAHxaez-JDKoqVMz5KTUoWIbjMVDB_wzyO0')
DEEPSEEK_API_KEY = os.getenv('sk-2850aebc4d6f4f66b839bd761bf5f083')
CHANNEL_ID = os.getenv('-1003030620712')  # ID вашего канала
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

if not BOT_TOKEN or not BOT_TOKEN.startswith('') or ':' not in BOT_TOKEN:
    logger.error(f"Неверный формат токена: {BOT_TOKEN}")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
    🤖 Привет! Я HiveMind — AI-помощник для анализа Telegram-каналов.

    Я могу:
    • Анализировать комментарии на токсичность
    • Выявлять основные темы обсуждений
    • Предлагать идеи для контента

    Для начала работы добавь меня в канал как администратора!
    """
    await update.message.reply_text(welcome_text)

async def analyze_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ комментария с помощью DeepSeek"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите текст для анализа после команды /analyze")
        return
        
    comment_text = " ".join(context.args)
    
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
                "content": "Ты — AI-модератор. Проанализируй комментарий на предмет токсичности, спама или нарушений. Ответь кратко."
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
        logger.error(f"Ошибка при запросе к DeepSeek: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при анализе. Попробуйте позже.")

async def monitor_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает мониторинг указанного канала"""
    try:
        # Получаем последние сообщения из канала
        messages = await context.bot.get_chat_history(chat_id=CHANNEL_ID, limit=10)
        
        analysis_results = []
        async for message in messages:
            if message.text and not message.from_user.is_bot:
                analysis = await analyze_message(message.text)
                if analysis:
                    analysis_results.append({
                        'message': message.text[:100] + "..." if len(message.text) > 100 else message.text,
                        'analysis': analysis
                    })
        
        # Формируем отчет
        if analysis_results:
            report = "📊 Отчет по анализу канала:\n\n"
            for i, result in enumerate(analysis_results, 1):
                report += f"{i}. {result['message']}\nАнализ: {result['analysis']}\n\n"
            
            await update.message.reply_text(report)
        else:
            await update.message.reply_text("Не удалось проанализировать сообщения в канале.")
            
    except Exception as e:
        logger.error(f"Ошибка при мониторинге канала: {e}")
        await update.message.reply_text("❌ Ошибка при доступе к каналу. Убедитесь, что бот добавлен как администратор.")

async def analyze_message(text):
    """Анализирует сообщение с помощью DeepSeek"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Проанализируй сообщение из Telegram-канала. Определи тональность, основные темы и дай краткую оценку."
            },
            {
                "role": "user",
                "content": f"Проанализируй это сообщение: '{text}'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Ошибка при анализе сообщения: {e}")
        return None

async def setup_channel(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет настройки канала"""
    try:
        chat = await context.bot.get_chat(chat_id=CHANNEL_ID)
        logger.info(f"Бот имеет доступ к каналу: {chat.title}")
        return True
    except Exception as e:
        logger.error(f"Ошибка доступа к каналу: {e}")
        return False

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_comment))
    application.add_handler(CommandHandler("monitor", monitor_channel))
    
    # Проверяем настройки канала при запуске
    application.job_queue.run_once(
        lambda context: asyncio.create_task(setup_channel(context)),
        when=5
    )
    
    # Запускаем бота
    application.run_polling()
    logger.info("Бот запущен!")

if __name__ == '__main__':
    import asyncio
    main()
