import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict

# Жестко заданные значения (замените на свои реальные значения)
BOT_TOKEN = '8217261903:AAHxaez-JDKoqVMz5KTUoWIbjMVDB_wzyO0'  # Ваш токен бота
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"  # Актуальный URL уточните в документации!
GIGACHAT_API_KEY = "MDE5OTVlMWUtNmZhMi03YmQ1LTgyZWUtY2E1MjFhNTA5YzI3OjJmNGI3M2E0LWVmZDgtNGFmOS1iODFhLTVmOThmMzczMmQ5NQ=="  # Ваш OAuth-токен
CHANNEL_ID = '-1001234567890'  # ID вашего канала (начинается с -100)
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
GIGACHAT_API_KEY = "MDE5OTVlMWUtNmZhMi03YmQ1LTgyZWUtY2E1MjFhNTA5YzI3OjJmNGI3M2E0LWVmZDgtNGFmOS1iODFhLTVmOThmMzczMmQ5NQ=="  # Замените на ваш реальный ключ
GIGACHAT_MODEL = "GIGACHAT_API_PERS"  # Или "GigaChat-Plus" для более мощной версии
CHANNEL_ID = "01995e1e-6fa2-7bd5-82ee-ca521a509c27"  # В формате -1001234567890

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
    """Анализ комментария с помощью GigaChat API"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите текст для анализа после команды /analyze")
        return
        
    comment_text = " ".join(context.args)
    
    # Подготовка запроса к GigaChat API
    headers = {
        "Authorization": f"Bearer {GIGACHAT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GIGACHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты — AI-модератор для Telegram-канала. Проанализируй комментарий на предмет токсичности, спама или нарушений. Ответь кратко и по делу."
            },
            {
                "role": "user",
                "content": f"Проанализируй этот комментарий из Telegram-канала: '{comment_text}'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        logger.info(f"Отправка запроса к GigaChat API: {comment_text[:50]}...")
        response = requests.post(GIGACHAT_API_URL, json=payload, headers=headers, timeout=30)
        
        # Проверяем статус ответа
        if response.status_code != 200:
            error_detail = f"Status: {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_detail += f", Message: {error_json['error'].get('message', 'Unknown error')}"
            except:
                error_detail += f", Response: {response.text[:200]}"
            
            logger.error(f"Ошибка API GigaChat: {error_detail}")
            
            # Более информативное сообщение для пользователя
            if response.status_code == 401:
                await update.message.reply_text("❌ Ошибка аутентификации. Проверьте API-ключ GigaChat.")
            elif response.status_code == 429:
                await update.message.reply_text("❌ Превышен лимит запросов к GigaChat API.")
            elif response.status_code == 500:
                await update.message.reply_text("❌ Внутренняя ошибка сервера GigaChat. Попробуйте позже.")
            else:
                await update.message.reply_text(f"❌ Ошибка при обращении к сервису анализа (код: {response.status_code}).")
            return
            
        result = response.json()
        
        # Проверяем структуру ответа (GigaChat может использовать немного другую структуру)
        if 'choices' not in result or len(result['choices']) == 0:
            logger.error(f"Неожиданный формат ответа от GigaChat: {result}")
            await update.message.reply_text("⚠️ Получен неожиданный ответ от сервиса анализа.")
            return
            
        # Извлекаем ответ (структура может отличаться от DeepSeek)
        ai_response = result['choices'][0]['message']['content']
        logger.info(f"Получен ответ от GigaChat: {ai_response[:100]}...")
        
        await update.message.reply_text(f"🔍 Результат анализа:\n\n{ai_response}")
        
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к GigaChat API")
        await update.message.reply_text("⚠️ Сервис анализа не отвечает. Попробуйте позже.")
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с GigaChat API")
        await update.message.reply_text("⚠️ Ошибка соединения с сервисом анализа.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к GigaChat: {e}")
        await update.message.reply_text("⚠️ Произошла непредвиденная ошибка при анализе.")
async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Автоматически анализирует сообщения в канале"""
    # Проверяем, что сообщение из нужного канала
    if update.message.chat.id != int(CHANNEL_ID):
        return
        
    # Пропускаем сообщения от самого бота
    if update.message.from_user and update.message.from_user.is_bot:
        return
        
    comment_text = update.message.text
    if not comment_text:
        return
        
    logger.info(f"Анализируем сообщение в канале: {comment_text[:50]}...")
    
    # Анализ с помощью GigaChat
    headers = {
        "Authorization": f"Bearer {GIGACHAT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GIGACHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты — AI-модератор для Telegram-канала. Проанализируй комментарий на предмет токсичности, спама или нарушений. Вердикт: ОДОБРЕНО, ПРЕДУПРЕЖДЕНИЕ или УДАЛИТЬ."
            },
            {
                "role": "user",
                "content": f"Проанализируй этот комментарий: '{comment_text}'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(GIGACHAT_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                analysis = result['choices'][0]['message']['content']
                
                # Простой анализ ответа
                if "УДАЛИТЬ" in analysis:
                    await update.message.delete()
                    logger.info("Сообщение удалено по результатам анализа.")
                elif "ПРЕДУПРЕЖДЕНИЕ" in analysis:
                    await update.message.reply_text("⚠️ Сообщение получило предупреждение от модератора.")
                    
    except Exception as e:
        logger.error(f"Ошибка при автоматическом анализе: {e}")


def main():
    """Запуск бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("analyze", analyze_comment))
        
        # Добавляем обработчик сообщений канала
        application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.CHANNEL, handle_channel_message))
        
        # Запускаем бота
        application.run_polling()
        logger.info("Бот запущен!")
        
    except Conflict as e:
        logger.error(f"Обнаружен конфликт: {e}. Возможно, бот уже запущен в другом месте.")
        # Можно добавить автоматическую перезагрузку через несколько секунд
        import time
        time.sleep(10)
        main()  # Перезапускаем бота
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")

if __name__ == '__main__':
    main()
