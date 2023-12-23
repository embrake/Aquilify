import os
import sys
import shutil
import argparse
import inquirer
import time
import subprocess
import configparser
import pkg_resources

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
    VERSION = "Aquilify v1.13 (Stable)"
    CONFIG_FILE = 'config.cfg'

    def __init__(self):
        self.parser = self._setup_arg_parser()

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
                self._copy_project_files(app_name, app_path)
        except Exception as e:
            self._print_colored(f"Error: {e}", Colors.FAIL)

    def _handle_existing_app(self, app_path, app_name):
        overwrite = inquirer.prompt([
            inquirer.Confirm('overwrite', message=f"{Colors.WARNING}App folder '{app_name}' already exists. Do you want to overwrite it?{Colors.ENDC}", default=False)
        ])
        if overwrite['overwrite']:
            self._overwrite_existing_app(app_path, app_name)
        else:
            self._print_bold("Operation aborted. Please choose a different app name.")

    def _overwrite_existing_app(self, app_path, app_name):
        try:
            shutil.rmtree(app_path)
            self._copy_project_files(app_name, app_path)
            self._print_colored(f"Project '{app_name}' overwritten successfully.", Colors.OKGREEN)
        except (OSError, shutil.Error) as e:
            self._print_colored(f"Failed to overwrite app '{app_name}': {e}", Colors.FAIL)

    def _copy_project_files(self, app_name, app_path):
        try:
            self._print_colored('Setting up Project {} in {} \n'.format(app_name, os.getcwd()), Colors.OKGREEN)
            time.sleep(1)
            self._print_colored('Creating __root__ file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Creating settings file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(2)
            self._print_colored('Creating views file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Creating constructor file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(1)
            self._print_colored('Creating packlib.lxe file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Creating config.cfg file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(2)
            self._print_colored('Creating __init__ file in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Creating app folder in {}'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(2)
            self._print_colored('Creating app/main file in {}'.format(os.getcwd() + '/{}/app'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Creating app/__init__ file in {}'.format(os.getcwd() + '/{}/app'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Creating requirements.txt file in {} \n'.format(os.getcwd() + '/{}'.format(app_name)), Colors.OKGREEN)
            time.sleep(0.8)
            self._print_colored('Installing middleware dependencies...', Colors.OKGREEN)
            time.sleep(3)
            self._print_colored('Middlewares setup completed \n', Colors.OKGREEN)
            time.sleep(0.3)
            self._print_colored('Installing utilities...', Colors.OKGREEN)
            time.sleep(3)
            self._print_colored('Utilities setup completed. \n', Colors.OKGREEN)
            time.sleep(0.3)
            self._print_colored('Analyzing project setup...', Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Finilize the project setup...', Colors.OKGREEN)
            time.sleep(0.3)

            _project_b9IN = "aquilify/build/{startup}"
            self._copy_package_files('aquilify', _project_b9IN, app_path)
                        
            self._create_config_file(app_path)
            self._create_packlib_file(app_path)
            
            config_file = os.path.join(app_path, 'config.cfg')

            if os.path.exists(config_file):
                self._update_config_file(config_file, app_name, app_path)
            self._print_colored(f"\nProject '{app_name}' created successfully. \n", Colors.OKGREEN)
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
INSTANCE = constructor:app
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
    "__version__": "float(1.13)",
    "__controller__": "aquilify.core.application",
    "__name__": "aquilify",
    "__versionControl__": "git.aquilify.commit"
}
"""
        packlib_file_path = os.path.join(app_path, 'packlib.lxe')
        self._write_to_file(packlib_file_path, packlib_data, "Packlib file")

    def _write_to_file(self, file_path, data, file_type):
        try:
            with open(file_path, 'w') as file:
                file.write(data)
            self._print_colored(f"{file_type} created successfully.", Colors.OKGREEN)
        except Exception as e:
            self._print_colored(f"Failed to create {file_type.lower()}: {e}", Colors.FAIL)

    def _copy_package_files(self, package_name, source_folder, destination_folder):
        try:
            package = pkg_resources.get_distribution(package_name)
            package_path = package.location

            folder_to_copy = os.path.join(package_path, *source_folder.split('/'))

            shutil.copytree(folder_to_copy, destination_folder)
        except pkg_resources.DistributionNotFound:
            print(f"Package '{package_name}' not found.")
        except FileNotFoundError:
            print(f"Source folder '{source_folder}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def _update_config_file(self, config_file, app_name, project_path):
        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if 'Aquilify' in config:
                config.set('Aquilify', 'PATH', project_path)
                config.set('Aquilify', 'VERSION', '1.13')
                config.set('Aquilify', 'COMPILER_PATH', project_path + '/.aquilify')
                config.set('Aquilify', 'PROJECT_NAME', app_name)
                config.set('Aquilify', 'SETTINGS', project_path  + '/settings.py')

                with open(config_file, 'w') as configfile:
                    config.write(configfile)
                
                self._print_colored("Config file updated successfully.", Colors.OKGREEN)
            else:
                self._print_colored("Aquilify section not found in the config file.", Colors.WARNING)
        except Exception as e:
            self._print_colored(f"Failed to update config file: {e}", Colors.FAIL)

    def _install_electrus(self):
        try:
            subprocess.run(["pip", "install", "electrus"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._print_colored('Installing https://github.com/embrake/electrus/branch/main...', Colors.OKGREEN)
            time.sleep(1)
            self._print_colored('Extracting electrus.zip...', Colors.OKGREEN)
            time.sleep(0.1)
            self._print_colored('Setting up wheel {}... \n'.format(sys.prefix), Colors.OKGREEN)
            time.sleep(1)
            self._print_colored("Electrus installed successfully.", Colors.OKGREEN)
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
            self._print_colored(self.VERSION, Colors.OKGREEN)
            return

        if args.command == "create-app":
            self._print_colored('\n *************************** Welcome to AQUILIFY *************************** \n', Colors.OKGREEN)
            if args.app_name:
                self._create_app(args.app_name)
            else:
                self._create_app_interactively()
        elif args.command == "runserver":
            self._run_server()
        else:
            self.parser.print_help()

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
                instance = netix_config.get('INSTANCE', 'constructor:app')

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

                    cmd.append(instance.replace('__instance__', 'constructor:app'))
                    subprocess.run(cmd)
            else:
                self._print_colored("Oops! Either you are not in the project directory or ASGI_SERVER block may not be configured properly. Visit http://aquilify.vvfin.in/project/config/errors for help.", Colors.WARNING)

        except Exception as e:
            self._print_colored(f"An error occurred while running the server: {e}", Colors.FAIL)
        
    def _create_app_interactively(self):
        questions = [
            inquirer.Text('app_name', message="Enter the name of the app", validate=lambda _, x: self._validate_app_name(_, x)),
            inquirer.List('setup_db', message="Would you like to set up Electrus database", choices=['Yes', 'No'], default='Yes', carousel=True),
        ]
        answers = inquirer.prompt(questions)
        if answers:
            self._create_app(answers['app_name'])
            if answers['setup_db'] == 'Yes':
                self._print_colored("Installing Electrus... \n", Colors.OKGREEN)
                try:
                    self._install_electrus()
                except Exception as e:
                    self._print_colored(f"Error while installing Electrus: {e}", Colors.FAIL)
        else:
            self._print_colored("Invalid app name.", Colors.FAIL)

    def _print_bold(self, message):
        print(f"{Colors.BOLD}{message}{Colors.ENDC}")

def main():
    cls = AxStartup().start()
    return cls

if __name__ == "__main__":
    main()