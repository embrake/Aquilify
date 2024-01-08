from aquilify.settings import settings
from aquilify.utils.module_loading import import_string


def default_storage(request):
    return import_string(settings.MESSAGE_STORAGE)(request)
