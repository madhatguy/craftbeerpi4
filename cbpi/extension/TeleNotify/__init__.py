import requests
from cbpi.api import *
from cbpi.api.config import ConfigType
import logging
import asyncio

logger = logging.getLogger(__name__)


class TeleNotify(CBPiExtension):

    def __init__(self, cbpi):
        super().__init__(cbpi=cbpi)
        self._task = asyncio.create_task(self.run())
        self.token = None
        self.chat_id = None
        self.is_init = False
        self.cbpi = cbpi
        self.listener_ID = None
        cbpi.app.on_startup.append(self.register_telegram_notifier)
        self.cbpi.register(self)

    async def telegram_bot_token(self):
        self.token = self.cbpi.config.get("TELEGRAM_BOT_TOKEN")
        if self.token is None:
            print("INIT Telegram Bot Token")
            try:
                await self.cbpi.config.add("TELEGRAM_BOT_TOKEN", "", ConfigType.STRING, "Telegram Bot Token")
            except:
                self.cbpi.notify("Telegram Error", "Unable to update database. Update CraftBeerPi and reboot.",
                                 type="danger")

    async def telegram_chat_id(self):
        self.chat_id = self.cbpi.config.get("TELEGRAM_CHAT_ID")
        if self.chat_id is None:
            print("INIT Telegram Chat ID")
            try:
                await self.cbpi.config.add("TELEGRAM_CHAT_ID", "", ConfigType.STRING, "Telegram Chat ID")
            except:
                self.cbpi.notify("Telegram Error", "Unable to update database. Update CraftBeerPi and reboot.",
                                 type="danger")

    @on_startup('reg_telegram', order=9000)
    async def register_telegram_notifier(self, *args):
        self.cbpi.app.logger.info("INITIALIZE Telegram PLUGIN")
        await self.telegram_bot_token()
        await self.telegram_chat_id()
        if self.token is None or not self.token:
            self.cbpi.notify("Telegram", "Check that Telegram Bot Token is set", type="danger")
        elif self.chat_id is None or not self.chat_id:
            self.cbpi.notify("Telegram", "Check that Telegram Chat ID is set", type="danger")
        else:
            self.is_init = True

    async def run(self):
        logger.info('Starting Telegram Notifications background task')
        if self.token is None or self.token == "" or not self.token:
            logger.warning('Check Telegram API Token is set')
        elif self.chat_id is None or self.chat_id == "" or not self.chat_id:
            logger.warning('Check Telegram User Key is set')
        else:
            self.listener_ID = self.cbpi.notification.add_listener(self.messageEvent)
            logger.info("Telegram Listener ID: {}".format(self.listener_ID))
        return

    async def messageEvent(self, cbpi, title, message, type, action):
        if self.is_init:
            print(self.token, title)
            text = "<b>" + title + "</b>\n<i>" + message + "</i>"
            url = "https://api.telegram.org/bot" + self.token + "/sendMessage"
            escaped_url = requests.Request('GET', url, params={"chat_id": self.chat_id, "text": text,
                                                               "parse_mode": "HTML"}, ).prepare().url
            requests.get(escaped_url)


def setup(cbpi):
    '''
    This method is called by the server during startup
    Here you need to register your plugins at the server

    :param cbpi: the cbpi core
    :return:
    '''
    cbpi.plugin.register("TeleNotify", TeleNotify)
