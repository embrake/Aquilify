import json

from .base import BaseStorage
from .cookie import MessageDecoder, MessageEncoder
from aquilify.exception.base import ImproperlyConfigured


class SessionStorage(BaseStorage):

    session_key = "_messages"

    def __init__(self, request, *args, **kwargs):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The session-based temporary message storage requires session "
                "middleware to be installed, and come before the message "
                "middleware in the STAGE_HANDLERS list."
            )
        super().__init__(request, *args, **kwargs)

    def _get(self, *args, **kwargs):
        return (
            self.deserialize_messages(self.request.session.get(self.session_key)),
            True,
        )

    def _store(self, messages, response, *args, **kwargs):
        if messages:
            self.request.session[self.session_key] = self.serialize_messages(messages)
        else:
            self.request.session.delete(self.session_key)
        return []

    def serialize_messages(self, messages):
        encoder = MessageEncoder()
        return encoder.encode(messages)

    def deserialize_messages(self, data):
        if data and isinstance(data, str):
            return json.loads(data, cls=MessageDecoder)
        return data
