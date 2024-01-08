from aquilify.settings import settings
from . import constants


def get_level_tags():
    return {
        **constants.DEFAULT_TAGS,
        **getattr(settings, "MESSAGE_TAGS", {}),
    }
