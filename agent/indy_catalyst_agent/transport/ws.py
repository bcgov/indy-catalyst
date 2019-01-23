import asyncio
import json
import logging
import socket
from typing import Callable

from aiohttp import web, WSMsgType

from . import BaseTransport
from ..connections.websocket import WebsocketConnection


class WsSetupError(Exception):
    pass


class Ws(BaseTransport):
    def __init__(self, host: str, port: int, message_router: Callable) -> None:
        self.host = host
        self.port = port
        self.message_router = message_router

        self.logger = logging.getLogger(__name__)
        self.message_queue = asyncio.Queue()

    async def start(self) -> None:
        app = web.Application()
        app.add_routes([web.get("/", self.inbound_message_handler)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.port)
        try:
            await site.start()
        except OSError:
            raise WsSetupError(
                f"Unable to start webserver with host '{self.host}' and port '{self.port}'\n"
            )

    async def inbound_message_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Listen for incoming messages
        async for msg in ws:
            self.logger.info(f"Received message: {msg.data}")
            if msg.type == WSMsgType.TEXT:
                if msg.data == "close":
                    await ws.close()
                else:
                    try:
                        message_dict = json.loads(msg.data)
                    except json.decoder.JSONDecodeError as e:
                        error_message = f"Could not parse message json: {str(e)}"
                        self.logger.error(error_message)
                        await ws.send_json({"success": False, "message": error_message})
                        continue

                    try:
                        # Route message and provide connection instance as means to respond
                        await self.message_router(
                            message_dict,
                            WebsocketConnection(self.outbound_message_handler(ws)),
                        )

                    except Exception as e:
                        error_message = f"Error handling message: {str(e)}"
                        self.logger.error(error_message)
                        await ws.send_json({"success": False, "message": error_message})
                        continue

            elif msg.type == WSMsgType.ERROR:
                self.logger.error(
                    f"Websocket connection closed with exception {ws.exception()}"
                )

        self.logger.info("Websocket connection closed")
        return ws

    def outbound_message_handler(self, ws: web.WebSocketResponse):
        async def handle(message_dict: dict):
            self.logger.info(f"Sending message: {message_dict}")
            await ws.send_json(message_dict)

        return handle

