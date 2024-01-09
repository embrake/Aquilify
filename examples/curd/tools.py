import os

# Aquilify's command-line utility.

def main():
    os.environ.setdefault('AQUILIFY_SETTINGS_MODULE', 'settings')
    try:
        from aquilify.core.cmd import execute_from_cmd_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Aquilify. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_cmd_line()


if __name__ == '__main__':
    main()