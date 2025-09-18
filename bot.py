import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Жестко задаем токен (замените на ваш реальный токен)
BOT_TOKEN = '8217261903:AAHxaez-JDKoqVMz5KTUoWIbjMVDB_wzyO0'

# Остальные переменные (также можно заменить на жесткие значения)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-2850aebc4d6f4f66b839bd761bf5f083')
CHANNEL_ID = os.getenv('CHANNEL_ID', '-1003030620712')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

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
        logger.info(f"Отправка запроса к DeepSeek API: {comment_text[:50]}...")
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
        
        # Проверяем статус ответа
        if response.status_code != 200:
            logger.error(f"Ошибка API DeepSeek: {response.status_code} - {response.text}")
            await update.message.reply_text("⚠️ Ошибка при обращении к сервису анализа. Попробуйте позже.")
            return
            
        result = response.json()
        
        # Проверяем структуру ответа
        if 'choices' not in result or len(result['choices']) == 0:
            logger.error(f"Неожиданный формат ответа от DeepSeek: {result}")
            await update.message.reply_text("⚠️ Получен неожиданный ответ от сервиса анализа.")
            return
            
        ai_response = result['choices'][0]['message']['content']
        logger.info(f"Получен ответ от DeepSeek: {ai_response[:50]}...")
        
        await update.message.reply_text(f"🔍 Результат анализа:\n\n{ai_response}")
        
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к DeepSeek API")
        await update.message.reply_text("⚠️ Сервис анализа не отвечает. Попробуйте позже.")
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с DeepSeek API")
        await update.message.reply_text("⚠️ Ошибка соединения с сервисом анализа.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к DeepSeek: {e}")
        await update.message.reply_text("⚠️ Произошла непредвиденная ошибка при анализе.")

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_comment))
    
    # Запускаем бота
    application.run_polling()
    logger.info("Бот запущен!")
if __name__ == '__main__':
    main()
