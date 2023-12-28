"""
Backend for test environment.
"""

from ... import mail
from .base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(mail, "outbox"):
            mail.outbox = []

    def send_messages(self, messages):
        """Redirect messages to the dummy outbox"""
        msg_count = 0
        for message in messages:
            message.message()
            mail.outbox.append(message)
            msg_count += 1
        return msg_count
