from typing import List, Dict, Optional, Tuple, Any, Callable
import logging
import zlib
import base64

from . import WebSocket

class Channel:
    def __init__(self):
        self.connected_websockets: List[WebSocket] = []
        self.subscribed_channels: Dict[str, List[WebSocket]] = {}
        self.groups: Dict[str, List[WebSocket]] = {}
        self.message_history: Dict[WebSocket, List[str]] = {}
        self.message_queue: Dict[str, List[Tuple[str, str]]] = {}
        self.authenticated_websockets: Dict[WebSocket, Any] = {}
        self.event_listeners: Dict[str, List[Callable[[Any], Any]]] = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket, user: Optional[Any] = None):
        await websocket.accept()
        self.connected_websockets.append(websocket)
        self.message_history[websocket] = []
        self.authenticated_websockets[websocket] = user

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
        self.connected_websockets.remove(websocket)
        self._remove_from_subscriptions(websocket)
        del self.message_history[websocket]
        self.authenticated_websockets.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, channel_name: str):
        self.subscribed_channels.setdefault(channel_name, []).append(websocket)
        if channel_name in self.message_history:
            for message in self.message_history[websocket]:
                await websocket.send_text(message)
        if channel_name in self.message_queue:
            for sender, message in self.message_queue[channel_name]:
                await websocket.send_text(f"[{sender}] {message}")

    async def unsubscribe(self, websocket: WebSocket, channel_name: str):
        if channel_name in self.subscribed_channels:
            self.subscribed_channels[channel_name].remove(websocket)

    async def group_add(self, group_name: str, websocket: WebSocket):
        self.groups.setdefault(group_name, []).append(websocket)

    async def group_discard(self, group_name: str, websocket: WebSocket):
        if group_name in self.groups:
            self.groups[group_name].remove(websocket)

    async def group_send(self, group_name: str, message: str, sender: Optional[str] = None):
        if group_name in self.groups:
            for websocket in self.groups[group_name]:
                await websocket.send_text(message)

    async def send_to_user(self, user: Any, message: str):
        for websocket, auth_user in self.authenticated_websockets.items():
            if auth_user == user:
                await websocket.send_text(message)

    async def broadcast(self, message: str, sender: Optional[str] = None, compression: bool = False):
        try:
            for websocket in self.connected_websockets:
                await self._send_message(message, websocket, compression)
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {str(e)}")

    async def broadcast_to_channel(
        self, message: str, channel_name: str, sender: Optional[str] = None, compression: bool = False
    ):
        try:
            if channel_name in self.subscribed_channels:
                for websocket in self.subscribed_channels[channel_name]:
                    await self._send_message(message, websocket, compression)
        except Exception as e:
            self.logger.error(f"Error broadcasting to channel {channel_name}: {str(e)}")

    async def direct_message(self, message: str, recipient: WebSocket, sender: str):
        try:
            await recipient.send_text(f"[DM from {sender}] {message}")
        except Exception as e:
            self.logger.error(f"Error sending direct message: {str(e)}")

    def queue_message(self, sender: str, message: str, channel_name: str):
        self.message_queue.setdefault(channel_name, []).append((sender, message))

    def _remove_from_subscriptions(self, websocket: WebSocket):
        for ws_list in self.subscribed_channels.values():
            if websocket in ws_list:
                ws_list.remove(websocket)

    async def _send_message(self, message: str, websocket: WebSocket, compression: bool):
        try:
            if compression:
                compressed_message = zlib.compress(message.encode('utf-8'))
                compressed_message = base64.b64encode(compressed_message).decode('utf-8')
                await websocket.send_text(compressed_message)
            else:
                await websocket.send_text(message)
            self.message_history[websocket].append(message)
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")

    def add_event_listener(self, event_name: str, handler: Callable[[Any], Any]):
        self.event_listeners.setdefault(event_name, []).append(handler)

    async def emit_event(self, event_name: str, data: Any):
        if event_name in self.event_listeners:
            for handler in self.event_listeners[event_name]:
                try:
                    await handler(data)
                except Exception as e:
                    self.logger.error(f"Error handling event {event_name}: {str(e)}")
