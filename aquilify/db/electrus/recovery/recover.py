import os
import zipfile
import tarfile
import json
from typing import Optional, Dict, Any, Union

from..exception.base import ElectrusException
from .format import ZIP, JSON, TAR

class Recovery:
    def __init__(self, client: Any) -> None:
        self.client = client

    def backup(self, database: str, path: Optional[str] = None, format: Union[ZIP, TAR, JSON] = 'zip') -> str:
        try:
            if not self._is_database_exist(database):
                return f"Database '{database}' does not exist."

            if not path:
                path = os.path.join(os.getcwd(), 'backup')
                os.makedirs(path, exist_ok=True)

            backup_path = os.path.join(path, f'{database}.{format}')
            if format == 'zip':
                self._create_zip_backup(database, backup_path)
            elif format == 'tar':
                self._create_tar_backup(database, backup_path)
            elif format == 'json':
                self._create_json_backup(database, backup_path)
            else:
                raise ElectrusException("Unsupported backup format.")

            return f"Backup of '{database}' created at '{backup_path}'."
        except FileNotFoundError:
            return "Error creating backup: Database or backup path not found."
        except ElectrusException as e:
            return f"Error creating backup: {str(e)}"
        except Exception as e:
            return f"Error creating backup: {str(e)}"

    def _is_database_exist(self, database: str) -> bool:
        return os.path.exists(os.path.join(self.client.base_path, database))

    def _create_zip_backup(self, database: str, backup_path: str) -> None:
        source_dir = os.path.join(self.client.base_path, database)
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zip_file.write(file_path, arcname)

    def _create_tar_backup(self, database: str, backup_path: str) -> None:
        source_dir = os.path.join(self.client.base_path, database)
        with tarfile.open(backup_path, 'w') as tar_file:
            tar_file.add(source_dir, arcname=os.path.basename(source_dir))

    def _create_json_backup(self, database: str, backup_path: str) -> None:
        source_dir = os.path.join(self.client.base_path, database)
        data: Dict[str, Any] = {'database': database, 'files': {}}
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, source_dir)
                with open(file_path, 'rb') as f:
                    data['files'][relative_path] = f.read().decode('utf-8')

        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=4)

    def restore(self, path: str, format: str = 'zip') -> str:
        try:
            if format == 'zip':
                self._extract_zip_restore(path)
            elif format == 'tar':
                self._extract_tar_restore(path)
            elif format == 'json':
                self._extract_json_restore(path)
            else:
                raise ElectrusException("Unsupported backup format.")

            return f"Database restored from '{format}' backup."
        except FileNotFoundError:
            return "Error restoring database: Backup file not found."
        except ElectrusException as e:
            return f"Error restoring database: {str(e)}"
        except Exception as e:
            return f"Error restoring database: {str(e)}"

    def _extract_zip_restore(self, backup_path: str) -> None:
        if not os.path.exists(backup_path):
            raise FileNotFoundError("Backup file not found.")

        restored_folder = os.path.splitext(os.path.basename(backup_path))[0]
        target_path = os.path.join(os.path.expanduser("~"), '.electrus', restored_folder)

        os.makedirs(target_path, exist_ok=True)
        with zipfile.ZipFile(backup_path, 'r') as zip_file:
            zip_file.extractall(target_path)

    def _extract_tar_restore(self, backup_path: str) -> None:
        if not os.path.exists(backup_path):
            raise FileNotFoundError("Backup file not found.")

        restored_folder = os.path.splitext(os.path.basename(backup_path))[0]
        target_path = os.path.join(os.path.expanduser("~"), '.electrus', restored_folder)

        os.makedirs(target_path, exist_ok=True)
        with tarfile.open(backup_path, 'r') as tar_file:
            tar_file.extractall(target_path)

    def _extract_json_restore(self, backup_path: str) -> None:
        if not os.path.exists(backup_path):
            raise FileNotFoundError("Backup file not found.")

        with open(backup_path, 'r') as f:
            data: Dict[str, Any] = json.load(f)

        restored_folder = data['database']
        target_path = os.path.join(os.path.expanduser("~"), '.electrus', restored_folder)

        os.makedirs(target_path, exist_ok=True)
        for relative_path, content in data['files'].items():
            file_path = os.path.join(target_path, relative_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(content.encode('utf-8'))
