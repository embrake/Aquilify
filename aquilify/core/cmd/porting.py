import argparse
import logging
from aquilify.settings.base import settings
from aquilify.exception.base import ImproperlyConfigured
from aquilify.utils.module_loading import import_string
from aquilify.orm import connection

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CommandChoices:
    MAKE_PORTING = 'makeporting'

def get_models_from_settings():
    try:
        database_settings = getattr(settings, "DATABASE")
        default_settings = database_settings.get('default', {})
        return default_settings.get('MODELS', [])
    except AttributeError:
        raise ImproperlyConfigured("Database settings not configured properly!")

def load_models(models):
    loaded_models = []
    for index, model in enumerate(models, start=1):
        loaded_model = import_string(model)
        if not loaded_model:
            raise ImproperlyConfigured(f"Model '{model}' not found")
        loaded_models.append(loaded_model)
        print(f"{Colors.OKGREEN}{index}.{Colors.ENDC} Model {Colors.OKGREEN}'{loaded_model.__name__}'{Colors.ENDC} initiated successfully... {Colors.OKGREEN}200{Colors.ENDC}")
    return loaded_models

def create_porting(models):
    try:
        print('')
        for index, model in enumerate(models, start=1):
            print(f"{Colors.OKGREEN}{index}.{Colors.ENDC} Model {Colors.OKGREEN}'{model.__name__}'{Colors.ENDC} Applied successfully... {Colors.OKGREEN}200{Colors.ENDC}")
        with connection(tables=models) as _:
            return lambda: connection(models)
    except Exception as e:
        raise ImproperlyConfigured(f"Error creating porting: {e}")

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

def make_porting(parser: argparse.ArgumentParser):
    logger = setup_logging()
    parser.add_argument('command', choices=[CommandChoices.MAKE_PORTING], help='Command to execute')
    args = parser.parse_args()

    if args.command == CommandChoices.MAKE_PORTING:
        try:
            models = get_models_from_settings()
            loaded_models = load_models(models)
            create_porting(loaded_models)
        except ImproperlyConfigured as e:
            logger.error(str(e))
            raise
