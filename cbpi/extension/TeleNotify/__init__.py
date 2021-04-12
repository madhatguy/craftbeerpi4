import logging
import asyncio
from cbpi.api import *
from cbpi.api.config import ConfigType
import requests


logger = logging.getLogger(__name__)

telegram_token = None
telegram_user = None
telegram = None


class TeleNotify(CBPiExtension):

    def __init__(self, cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.run())

    async def run(self):
        logger.info('Starting Telegram Notifications background task')
        await self.TeleUser()
        await self.TeleToken()
        if telegram_token is None or telegram_token == "" or not telegram_token:
            logger.warning('Check Telegram API Token is set')
        elif telegram_user is None or telegram_user == "" or not telegram_user:
            logger.warning('Check Telegram User Key is set')
        else:
            self.listener_ID = self.cbpi.notification.add_listener(self.messageEvent)
            logger.info("Telegram Listener ID: {}".format(self.listener_ID))
        pass

    async def TeleToken(self):
        global telegram_token
        telegram_token = self.cbpi.config.get("telegram_token", None)
        if telegram_token is None:
            logger.info("INIT Telegram Token")
            try:
                await self.cbpi.config.add("telegram_token", "", ConfigType.STRING, "Telegram API Token")
            except:
                logger.warning('Unable to update config')

    async def TeleUser(self):
        global telegram_user
        telegram_user = self.cbpi.config.get("telegram_user", None)
        if telegram_user is None:
            logger.info("INIT Telegram User Key")
            try:
                await self.cbpi.config.add("telegram_user", "", ConfigType.STRING, "Telegram User Key")
            except:
                logger.warning('Unable to update config')

    async def messageEvent(self, cbpi, title, message, type, action):
        tele_data = {"token": telegram_token, "user": telegram_user}
        text = "<b>" + title + "</b>\n<i>" + message + "</i>"
        url = "https://api.telegram.org/bot" + tele_data["token"] + "/sendMessage"
        escaped_url = requests.Request('GET', url, params={"chat_id": tele_data["user"], "text": text,
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
