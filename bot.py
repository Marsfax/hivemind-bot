import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict

# Жестко заданные значения (замените на свои реальные значения)
BOT_TOKEN = '8217261903:AAHxaez-JDKoqVMz5KTUoWIbjMVDB_wzyO0'  # Ваш токен бота
DEEPSEEK_API_KEY = 'sk-your-deepseek-api-key-here'  # Ваш API-ключ DeepSeek
CHANNEL_ID = '-1001234567890'  # ID вашего канала (начинается с -100)
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        logger.info(f"Отправка запроса к DeepSeek API: {comment_text[:50]}...")
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
        
        # Детальная проверка ответа
        logger.info(f"Статус ответа: {response.status_code}")
        logger.info(f"Заголовки ответа: {dict(response.headers)}")
        
        # Проверяем статус ответа
        if response.status_code != 200:
            error_detail = f"Status: {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_detail += f", Message: {error_json['error'].get('message', 'Unknown error')}"
                    error_detail += f", Type: {error_json['error'].get('type', 'Unknown')}"
            except:
                error_detail += f", Response: {response.text[:200]}"
            
            logger.error(f"Ошибка API DeepSeek: {error_detail}")
            
            # Более информативное сообщение для пользователя
            if response.status_code == 401:
                await update.message.reply_text("❌ Ошибка аутентификации. Проверьте API-ключ DeepSeek.")
            elif response.status_code == 429:
                await update.message.reply_text("❌ Превышен лимит запросов к DeepSeek API.")
            elif response.status_code == 500:
                await update.message.reply_text("❌ Внутренняя ошибка сервера DeepSeek. Попробуйте позже.")
            else:
                await update.message.reply_text(f"❌ Ошибка при обращении к сервису анализа (код: {response.status_code}).")
            return
            
        result = response.json()
        
        # Проверяем структуру ответа
        if 'choices' not in result or len(result['choices']) == 0:
            logger.error(f"Неожиданный формат ответа от DeepSeek: {result}")
            await update.message.reply_text("⚠️ Получен неожиданный ответ от сервиса анализа.")
            return
            
        ai_response = result['choices'][0]['message']['content']
        logger.info(f"Получен ответ от DeepSeek: {ai_response[:100]}...")
        
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
    max_retries = 5
    retry_delay = 10  # секунды
    
    for attempt in range(max_retries):
        try:
            # Создаем приложение
            application = Application.builder().token(BOT_TOKEN).build()
            
            # Добавляем обработчики команд
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("analyze", analyze_comment))
            
            # Запускаем бота
            logger.info(f"Попытка запуска бота ({attempt + 1}/{max_retries})...")
            application.run_polling(drop_pending_updates=True)
            logger.info("Бот запущен!")
            break
            
        except Conflict as e:
            logger.error(f"Обнаружен конфликт: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Повторная попытка через {retry_delay} секунд...")
                import time
                time.sleep(retry_delay)
            else:
                logger.error("Достигнуто максимальное количество попыток. Бот остановлен.")
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            break

if __name__ == '__main__':
    main()
