import os
import re
import shutil
import argparse
import time
import subprocess
import configparser

from .fax import settings, views, asgi, __root__, routing, ax, tools, models
from .fax.app import main as mainview

from .insecure import ax_insecure_key

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class AxStartup:
    VERSION = ax.AX_VERSION
    CONFIG_FILE = 'config.cfg'

    def __init__(self):
        self.parser = self._setup_arg_parser()
        
    def measure_time(self, func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            return elapsed_time
        return wrapper
    
    def create_file(self, file_path, content=None):
        try:
            with open(file_path, 'a') as f:
                if content:
                    f.write(content)
        except Exception as e:
            raise e

    def _setup_arg_parser(self):
        parser = argparse.ArgumentParser(description="Create an app with specified name and copy project files.")
        parser.add_argument("-v", "--version", action="store_true", help="Display Aquilify version")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        create_app_parser = subparsers.add_parser("create-app", help="Create an app")
        create_app_parser.add_argument("app_name", nargs='?', default=None, help="Name of the app to be created (optional)")

        run_server_parser = subparsers.add_parser("runserver", help="Run the server")

        return parser

    def _print_colored(self, message, color):
        print(f"{color}{message}{Colors.ENDC}")

    def _create_app(self, app_name):
        app_path = os.path.join(os.getcwd(), app_name)
        try:
            if os.path.exists(app_path):
                self._handle_existing_app(app_path, app_name)
            else:
                current_dir = os.getcwd()
                project_dir = os.path.join(current_dir, app_name)
                os.makedirs(project_dir, exist_ok=True)
                self._copy_project_files(app_name, app_path)
        except Exception as e:
            self._print_colored(f"Error: {e}", Colors.FAIL)

    def _handle_existing_app(self, app_path, app_name):
        overwrite = str(input(f"{Colors.WARNING}App folder '{app_name}' already exists. Do you want to overwrite it?{Colors.ENDC} "))
        
        if overwrite in ("YES", 'Yes', 'Y', 'y'):
            self._overwrite_existing_app(app_path, app_name)
        else:
            self._print_bold("Operation aborted. Please choose a different app name.")

    def _overwrite_existing_app(self, app_path, app_name):
        try:
            shutil.rmtree(app_path)
            current_dir = os.getcwd()
            project_dir = os.path.join(current_dir, app_name)
            os.makedirs(project_dir, exist_ok=True)
            self._copy_project_files(app_name, app_path)
            self._print_colored(f"Project '{app_name}' overwritten successfully.", Colors.OKGREEN)
        except (OSError, shutil.Error) as e:
            self._print_colored(f"Failed to overwrite app '{app_name}': {e}", Colors.FAIL)

    def _copy_project_files(self, app_name, app_path):
        try:
            self._copy_package_files(app_name, app_path)
                        
            self._create_config_file(app_path)
            self._create_packlib_file(app_path)
            
            config_file = os.path.join(app_path, 'config.cfg')

            if os.path.exists(config_file):
                self._update_config_file(config_file, app_name, app_path)
            print(f"\nProject '{Colors.OKGREEN}{app_name}{Colors.ENDC}' created successfully. \n")
        except (OSError, shutil.Error) as e:
            self._print_colored(f"Failed to create app '{app_name}': {e}", Colors.FAIL)

    def _create_config_file(self, app_path):
        config_data = """[Aquilify]
PATH = ""
PROJECT_NAME = ""
VERSION = ""
COMPILER_PATH = ""
SETTINGS = ""

[ASGI_SERVER]
SERVER = NETIX
HOST = 127.0.0.1
PORT = 8000
DEBUG = True
RELOAD = False
INSTANCE = asgi:application
"""
        config_file_path = os.path.join(app_path, 'config.cfg')
        self._write_to_file(config_file_path, config_data, "Config file")

    def _create_packlib_file(self, app_path):
        packlib_data = """# This is an aquilify environment which is used to connect the application with secret variables.
# This is only built for system usage so, don't make any changes to the default configuration.

# Warning - If you make any changes to the default environment, it may affect your application and even break the routing.

# Inbuilt environment module of LxEnvironment...

import { environment } from 'LxEnvironment.env'

# Feed the export function to builder and configure the secret environment variables.

environment.export => (builder) = {
    "sysMenSecretKey": "str(base64.encode('utf-8'))",
    "sysEnvironmentPath": "os.path.join('/{folder}/{project}', '.aquilify')",
    "sysEnvironmentSettings": "settings.py",
    "__version__": "float(1.14)",
    "__controller__": "aquilify.core.application",
    "__name__": "aquilify"
}
"""
        packlib_file_path = os.path.join(app_path, 'packlib.lxe')
        self._write_to_file(packlib_file_path, packlib_data, "Packlib file")

    def _write_to_file(self, file_path, data, file_type):
        try:
            with open(file_path, 'w') as file:
                file.write(data)
            print(f"{file_type} {file_path} ...{Colors.OKGREEN}200{Colors.ENDC}")
        except Exception as e:
            self._print_colored(f"Failed to create {file_type.lower()}: {e}", Colors.FAIL)
    
    def _copy_package_files(self, app_name, app_path):
        try:
            files = ['__init__.py', 'views.py', 'settings.py', 'asgi.py', 'models.py', 'tools.py', 'routing.py', '__root__.py', 'config.cfg', 'packlib.lxe']
            total_time = 0

            for file in files:
                file_path = os.path.join(app_path, file)
                try:
                    content = None
                    if file == 'settings.py':
                        content = settings.SETTINGS % ax_insecure_key()
                    elif file == 'views.py':
                        content = views.VIEWS
                    elif file == '__root__.py':
                        content = __root__.ROOT
                    elif file == 'routing.py':
                        content = routing.ROUTING
                    elif file == 'asgi.py':
                        content = asgi.ASGI
                    elif file == 'tools.py':
                        content = tools.TOOLS
                    elif file == 'models.py':
                        content = models.MODLES

                    self.create_file(file_path, content)
                    elapsed_time = self.measure_time(self.create_file)(file_path)
                    total_time += elapsed_time

                    print(f"Created file: {file_path} ...{Colors.OKGREEN}200{Colors.ENDC}")
                except Exception as e:
                    raise e
            for folder_name in ['app', 'lifespan']:
                folder_path = os.path.join(app_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                print(f"Created folder: {folder_path} ...{Colors.OKGREEN}200{Colors.ENDC}")
                
                if folder_name == 'app':
                    main_py_path = os.path.join(folder_path, 'main.py')
                    self.create_file(main_py_path, mainview.SCHEMATIC)
                    self.create_file(os.path.join(folder_path, '__init__.py'))
                    print(f"Created folder: {main_py_path} ...{Colors.OKGREEN}200{Colors.ENDC}")
                elif folder_name == 'lifespan':
                    self.create_file(os.path.join(folder_path, '__init__.py'))
                    print(f"Created file: {os.path.join(folder_path, '__init__.py')} ...{Colors.OKGREEN}200{Colors.ENDC}")
                    
        except Exception as e:
            print(f"An error occurred: {e}")

    def _update_config_file(self, config_file, app_name, project_path):
        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if 'Aquilify' in config:
                config.set('Aquilify', 'PATH', project_path)
                config.set('Aquilify', 'VERSION', '1.14')
                config.set('Aquilify', 'COMPILER_PATH', project_path + '/.aquilify')
                config.set('Aquilify', 'PROJECT_NAME', app_name)
                config.set('Aquilify', 'SETTINGS', project_path  + '/settings.py')

                with open(config_file, 'w') as configfile:
                    config.write(configfile)
                
                print(f"Update {config_file} ...{Colors.OKGREEN}200{Colors.ENDC}")
            else:
                self._print_colored("Aquilify section not found in the config file.", Colors.WARNING)
        except Exception as e:
            self._print_colored(f"Failed to update config file: {e}", Colors.FAIL)
            
    def _install_electrus(self):
        try:
            subprocess.run(["pip", "install", "electrus"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f'Installing https://pypi.org/project/electrus/ ...{Colors.OKGREEN}200{Colors.ENDC}')
            print(f"Electrus installed successfully ...{Colors.OKGREEN}200{Colors.ENDC}")
        except subprocess.CalledProcessError as e:
            self._print_colored(f"Failed to install Electrus: {e.stderr.decode('utf-8')}", Colors.FAIL)

    def _validate_app_name(self, answers, current_app_name):
        app_path = os.path.join(os.getcwd(), current_app_name)
        if os.path.exists(app_path):
            return f"An app with the name '{current_app_name}' already exists. Please choose a different name."
        return True

    def start(self):
        args = self.parser.parse_args()

        if args.version:
            for version in self.VERSION:              
                print(version)
            return  

        if args.command == "create-app":
            self._print_colored(ax.AQUILIFY_THEME, Colors.OKGREEN)
            if args.app_name:
                self._create_app(args.app_name)
            else:
                self._create_app_basic()
        elif args.command == "runserver":
            self._run_server()
        else:
            self.parser.print_help()
        
        return

    def _run_server(self):
        try:
            config = configparser.ConfigParser()
            config.read(self.CONFIG_FILE)

            if 'ASGI_SERVER' in config:
                netix_config = config['ASGI_SERVER']
                server = netix_config.get('SERVER', 'NETIX')
                host = netix_config.get('HOST', '127.0.0.1')
                port = netix_config.get('PORT', '8000')
                debug = netix_config.getboolean('DEBUG', fallback=False)
                reload = netix_config.getboolean('RELOAD', fallback=False)
                instance = netix_config.get('INSTANCE', 'routing:app')

                if server == 'NETIX':
                    cmd = ['netix']
                elif server == 'UVICORN':
                    cmd = ['uvicorn']
                else:
                    self._print_colored("Unsupported ASGI Server {} by Aquilify. Visit http://aquilify.vvfin.in/project/config/server for configuration details.".format(server), Colors.FAIL)
                    cmd = None

                if cmd:
                    if server == 'NETIX' and debug:
                        cmd.append('--debug')

                    if reload:
                        cmd.append('--reload')

                    if port:
                        cmd.append('--port')
                        cmd.append(port)

                    if host:
                        cmd.append('--host')
                        cmd.append(host)

                    cmd.append(instance.replace('__instance__', 'routing:app'))
                    subprocess.run(cmd)
            else:
                self._print_colored("Oops! Either you are not in the project directory or ASGI_SERVER block may not be configured properly. Visit http://aquilify.vvfin.in/project/config/errors for help.", Colors.WARNING)

        except Exception as e:
            self._print_colored(f"An error occurred while running the server, either {server} isn't installed or sys error!: {e}", Colors.FAIL)
        except KeyboardInterrupt as e:
            pass

    def _print_bold(self, message):
        print(f"{Colors.BOLD}{message}{Colors.ENDC}")
        
    def _create_app_basic(self):
        app_name = input("Enter the name of the app: ").strip()
        if not app_name:
            self._print_colored("App name can't be empty!", Colors.FAIL)
            return self._create_app_basic()

        if not re.match(r'^[\w\-.]+$', app_name):
            self._print_colored("Invalid project name. Use only letters, numbers, underscores, hyphens, and periods.", Colors.FAIL)
            return

        if not self._validate_app_name('', app_name):
            return

        setup_db = input("Would you like to set up Electrus database (Yes/No): ").strip().lower()
        
        if setup_db not in ("yes", "no"):
            self._print_colored("Invalid value received: {}. Use either Yes or No.".format(setup_db), Colors.FAIL)
            return

        if setup_db == "yes":
            self._print_colored("Installing Electrus... \n", Colors.OKGREEN)
            try:
                self._install_electrus()
            except Exception as e:
                self._print_colored(f"Error while installing Electrus: {e}", Colors.FAIL)

        self._create_app(app_name)
            
def main():
    cls = AxStartup().start()
    return cls

if __name__ == "__main__":
    main()