"""A connector for ICQ"""
import logging
import aiohttp
import asyncio
from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token"): str,
    Required("base-url"): str,
    "whitelisted-users": list,
}


class ConnectorICQ(Connector):
    """A connector for ICQ

    ICQ: https://icq.com/
    ICQ bot-api: https://icq.com/botapi/?lang=en
    """

    def __init__(self, config, opsdroid=None):
        """
        Create the connector.
        :param config (dict): configuration settings from the file configuration.yaml.
        :param opsdroid (OpsDroid): An instance of opsdroid.core.
        """
        _LOGGER.debug("Loaded ICQ Connector")
        super().__init__(config, opsdroid=opsdroid)
        self.name = "icq"
        self.opsdroid = opsdroid
        self.latest_update = None
        self.listening = True
        self.base_url = config.get("base-url", None)
        self.default_user = config.get("default-user", None)
        self.default_target = self.default_user
        self.whitelisted_users = config.get("whitelisted-users", None)
        _LOGGER.debug(self.whitelisted_users)
        self.update_interval = config.get("update-interval", 1)
        self.session = None
        self._closing = asyncio.Event()
        self.loop = asyncio.get_event_loop()
        try:
            self.token = config["token"]
        except (KeyError, AttributeError):
            _LOGGER.error(
                "Unable to login: Access token is missing. ICQ connector will be unavailable."
            )

    @staticmethod
    def get_user(response):
        """
        Get user from response.
        The API response is different depending on how
        the bot is set up and where the message is coming
        from. This method was created to keep if/else
        statements to a minium on _parse_message.
        :param response (str): Response returned by aiohttp.ClientSession.
        :param bot_name (str): Name of the bot used in opsdroid configuration.
        """
        nick = None
        user_id = None

        if "userId" in response.get("payload", {}).get("from", {}):
            user_id = response["payload"]["from"]["userId"]
        if "nick" in response.get("payload", {}).get("from", {}):
            nick = response["payload"]["from"]["nick"]

        return nick, user_id

    def handle_user_permission(self, nick, user_id):
        """
        Handle user permissions.
        This will check if the user that tried to talk with
        the bot is allowed to do so.
        """
        if (
            not self.whitelisted_users
            or nick in self.whitelisted_users
            or user_id in self.whitelisted_users
        ):
            return True

        return False

    def build_url(self, method) -> str:
        """
        Build the url to connect to the API.
        :param method (str): API call end point.
        :return: String that represents the full API url.
        """
        return f"https://{self.base_url}{method}"

    async def connect(self):
        """
        Connect to ICQ.
        Basically checks if provided token is valid.
        """
        _LOGGER.debug("Connecting to ICQ.")

        self.session = aiohttp.ClientSession()
        params = {"token": self.token}
        resp = await self.session.get(url=self.build_url("self/get"), params=params)

        if resp.status != 200:
            _LOGGER.error("Unable to connect.")
            _LOGGER.error(f"ICQ error {resp.status}, {resp.text}.")
        else:
            json = await resp.json()
            _LOGGER.debug(json)
            _LOGGER.debug(f"Connected to ICQ as {json['nick']}.")

    async def _parse_message(self, response):
        """
        Handle logic to parse a received message.
        Since everyone can send a private message to any user/bot
        in ICQ, this method allows to set a list of whitelisted
        users that can interact with the bot. If any other user tries
        to interact with the bot the command is not parsed and instead
        the bot will inform that user that he is not allowed to talk
        with the bot.
        We also set self.latest_update to +1 in order to get the next
        available message (or an empty {} if no message has been received
        yet) with the method self._get_messages().
        :param response (dict): Response returned by aiohttp.ClientSession.
        """

        _LOGGER.debug(response)
        for event in response.get("events", {}):
            _LOGGER.debug(event)
            payload = event.get("payload", {})
            if event.get("type", None) == "editedMessage":
                self.latest_update = event.get("eventId", None)
                _LOGGER.debug("editedMessage message - Ignoring message.")
            elif event.get("type", None) == "newMessage" and "text" in payload:
                nick, user_id = self.get_user(event)
                message = Message(
                    text=payload["text"],
                    user=nick,
                    user_id=user_id,
                    target=payload["chat"]["chatId"],
                    connector=self,
                )
                if self.handle_user_permission(nick, user_id):
                    await self.opsdroid.parse(message)
                else:
                    if "type" in payload.get("chat", {}):
                        if payload["chat"]["type"] == "private":
                            _LOGGER.debug(f'{payload["chat"]["type"]} - type of chat')
                            message.text = "Sorry, you're not allowed to speak with this bot."
                            await self.send(message)
                self.latest_update = event.get("eventId", None)
            elif "eventId" in event:
                self.latest_update = event.get("eventId", None)
                _LOGGER.debug("Ignoring event.")
            else:
                _LOGGER.error("Unable to parse the event.")

    async def _get_messages(self):
        """
        Connect to the ICQ API.
        Uses an aiohttp ClientSession to connect to ICQ API
        and get the latest messages from the chat service.
        The data["lastEventId"] is used to consume every new message, the API
        returns an  int - "update_id" value. In order to get the next
        message this value needs to be increased by 1 the next time
        the API is called. If no new messages exists the API will just
        return an empty {}.
        """
        data = {"token": self.token, "pollTime": 30, "lastEventId": 1}
        if self.latest_update is not None:
            data["lastEventId"] = self.latest_update

        await asyncio.sleep(self.update_interval)
        resp = await self.session.get(self.build_url("events/get"), params=data)

        if resp.status != 200:
            _LOGGER.error(f"ICQ error {resp.status}, {resp.text}.")
            self.listening = False
        else:
            json = await resp.json()
            await self._parse_message(json)

    async def get_messages_loop(self):
        """
        Listen for and parse new messages.
        The bot will always listen to all events from the server
        The method will sleep asynchronously at the end of
        every loop. The time can either be specified in the
        configuration.yaml with the param update-interval - this
        defaults to 1 second.
        """
        while self.listening:
            await self._get_messages()

    async def listen(self):
        """
        Listen method of the connector.
        Every connector has to implement the listen method. When an
        infinite loop is running, it becomes hard to cancel this task.
        So we are creating a task and set it on a variable, so we can
        cancel the task.
        """
        message_getter = self.loop.create_task(await self.get_messages_loop())
        await self._closing.wait()
        message_getter.cancel()

    @register_event(Message)
    async def send_message(self, message):
        """
        Respond with a message.
        :param message (object): An instance of Message.
        """
        _LOGGER.debug(
            f"Responding with: '{message.text}' at target: '{message.target}'"
        )

        data = dict()
        data["token"] = self.token
        data["chatId"] = message.target
        data["text"] = message.text
        resp = await self.session.post(self.build_url("messages/sendText"), data=data)
        if resp.status == 200:
            _LOGGER.debug("Successfully responded.")
        else:
            _LOGGER.error("Unable to respond.")

    async def disconnect(self):
        """
        Disconnect from ICQ.
        Stops the infinite loop found in self._listen(), closes
        aiohttp session.
        """
        self.listening = False
        self._closing.set()
        await self.session.close()
