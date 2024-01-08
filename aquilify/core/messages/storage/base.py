from aquilify.settings import settings
from .. import constants, utils
from aquilify.utils.functional import SimpleLazyObject

LEVEL_TAGS = SimpleLazyObject(utils.get_level_tags)


class Message:
    def __init__(self, level, message, extra_tags=None):
        self.level = int(level)
        self.message = message
        self.extra_tags = extra_tags

    def _prepare(self):
        self.message = str(self.message)
        self.extra_tags = str(self.extra_tags) if self.extra_tags is not None else None

    def __eq__(self, other):
        if not isinstance(other, Message):
            return NotImplemented
        return self.level == other.level and self.message == other.message

    def __str__(self):
        return str(self.message)

    def __repr__(self):
        extra_tags = f", extra_tags={self.extra_tags!r}" if self.extra_tags else ""
        return f"Message(level={self.level}, message={self.message!r}{extra_tags})"

    @property
    def tags(self):
        return " ".join(tag for tag in [self.extra_tags, self.level_tag] if tag)

    @property
    def level_tag(self):
        return LEVEL_TAGS.get(self.level, "")


class BaseStorage:
    def __init__(self, request, *args, **kwargs):
        self.request = request
        self._queued_messages = []
        self.used = False
        self.added_new = False
        super().__init__(*args, **kwargs)

    def __len__(self):
        return len(self._loaded_messages) + len(self._queued_messages)

    def __iter__(self):
        self.used = True
        if self._queued_messages:
            self._loaded_messages.extend(self._queued_messages)
            self._queued_messages = []
        return iter(self._loaded_messages)

    def __contains__(self, item):
        return item in self._loaded_messages or item in self._queued_messages

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: request={self.request!r}>"

    @property
    def _loaded_messages(self):
        if not hasattr(self, "_loaded_data"):
            messages, all_retrieved = self._get()
            self._loaded_data = messages or []
        return self._loaded_data

    def _get(self, *args, **kwargs):
        raise NotImplementedError(
            "subclasses of BaseStorage must provide a _get() method"
        )

    def _store(self, messages, response, *args, **kwargs):
        raise NotImplementedError(
            "subclasses of BaseStorage must provide a _store() method"
        )

    def _prepare_messages(self, messages):
        for message in messages:
            message._prepare()

    def update(self, response):
        self._prepare_messages(self._queued_messages)
        if self.used:
            return self._store(self._queued_messages, response)
        elif self.added_new:
            messages = self._loaded_messages + self._queued_messages
            return self._store(messages, response)

    def add(self, level, message, extra_tags=""):
        if not message:
            return
        level = int(level)
        if level < self.level:
            return
        self.added_new = True
        message = Message(level, message, extra_tags=extra_tags)
        self._queued_messages.append(message)

    def _get_level(self):
        if not hasattr(self, "_level"):
            self._level = getattr(settings, "MESSAGE_LEVEL", constants.INFO)
        return self._level

    def _set_level(self, value=None):
        """
        Set a custom minimum recorded level.

        If set to ``None``, the default level will be used (see the
        ``_get_level`` method).
        """
        if value is None and hasattr(self, "_level"):
            del self._level
        else:
            self._level = int(value)

    level = property(_get_level, _set_level, _set_level)
