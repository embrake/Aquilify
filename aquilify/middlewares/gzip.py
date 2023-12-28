import os
import gzip
import json
import logging
import uuid

from io import BytesIO
from ..settings.compression import CompressionSetting

class GzipMiddleware:
    def __init__(
        self
    ):
        self.compress_level = 6
        self.content_types = [
            'text/html',
            'text/css',
            'application/javascript',
            'application/json',
        ]
        self.ignore_content_length = None
        self.exclude_paths = []
        self.encodings = ['gzip']
        self.custom_compress_funcs = {}
        self.compression_folder = '.aquilify/compression/'
        self.config_file = '.aquilify/config.json'
        self.logger = self._setup_logger()
        self._create_aquilify_folder()
        self._create_compression_folder()

        self.settings = CompressionSetting._compression_settings()
        self.compress_level = self.settings['GZIP_COMPRESSION_LEVEL']
        self.content_types = self.settings['GZIP_COMPRESSION_CONTENT_TYPES']
        self.ignore_content_length = self.settings['GZIP_IGNORE_CONTENT_LENGHT']
        self.exclude_paths = self.settings['GZIP_EXCLUDE_PATHS']
        self.encodings = self.settings['GZIP_CONTENT_ENCODING']
        self.custom_compress_funcs = self.settings['GZIP_COMPRESSION_FUNCTION']

    def _setup_logger(self):
        logger = logging.getLogger('GzipMiddleware')
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        logger.addHandler(ch)
        return logger

    def _create_aquilify_folder(self):
        try:
            aquilify_folder = os.path.join(os.getcwd(), '.aquilify')
            if not os.path.exists(aquilify_folder):
                os.makedirs(aquilify_folder)
        except Exception as e:
            self.logger.error(f"Error creating '.aquilify' folder: {e}")

    def _create_compression_folder(self):
        try:
            compression_folder_path = os.path.join(os.getcwd(), self.compression_folder)
            if not os.path.exists(compression_folder_path):
                os.makedirs(compression_folder_path)
        except Exception as e:
            self.logger.error(f"Error creating '{self.compression_folder}' folder: {e}")

    async def __call__(self, request, response):
        try:
            if len(response.content) <= 50:
                return response
            
            if self._should_exclude_path(request.scope['path']):
                return response

            should_compress, content_type = self._should_compress(response)
            if should_compress:
                return response

            compressed_content = await self._compress_content(response.content, content_type)
            response.content = compressed_content
            response.headers.update(self._create_gzip_headers(compressed_content, content_type))

            self._save_compressed_data(compressed_content)
            self._update_config_file()
            self._cleanup_old_files()

        except Exception as e:
            self.logger.error(f"Error compressing response content: {e}")

        return response
    
    def _should_exclude_path(self, path):
        return any(path.startswith(excluded_path) for excluded_path in self.exclude_paths)

    def _should_compress(self, response):
        content_type = response.headers.get('Content-Type', '')
        encoding = response.headers.get('Content-Encoding', '')
        
        should_compress = (
            'Content-Encoding' not in response.headers and
            response.content and
            any(content_type.startswith(ct) for ct in self.content_types) and
            any(enc in self.encodings for enc in encoding.split(','))
        )
        return should_compress, content_type

    async def _compress_content(self, content, content_type):
        if content_type in self.custom_compress_funcs:
            return await self.custom_compress_funcs[content_type](content)

        if isinstance(content, (str, dict, list, tuple)):
            content = str(content).encode()
        elif not isinstance(content, bytes):
            raise ValueError("Unsupported response content type for compression")

        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='w', compresslevel=self.compress_level) as gz:
            gz.write(content)

        return buffer.getvalue()

    def _create_gzip_headers(self, compressed_content, content_type):
        headers = {
            'Content-Encoding': 'gzip',
            'Vary': 'Accept-Encoding'
        }
        if not self.ignore_content_length:
            headers['Content-Length'] = str(len(compressed_content))

        if content_type:
            headers['Content-Type'] = content_type

        return headers

    def _save_compressed_data(self, compressed_content):
        try:
            filename = self._generate_unique_filename()
            file_path = os.path.join(os.getcwd(), self.compression_folder, filename)
            with open(file_path, 'wb') as file:
                file.write(compressed_content)
        except Exception as e:
            self.logger.error(f"Error saving compressed data: {e}")

    def _generate_unique_filename(self):
        return str(uuid.uuid4()) + '.gzip'

    def _update_config_file(self):
        try:
            config_path = os.path.join(os.getcwd(), self.config_file)
            if not os.path.exists(config_path):
                config_data = {"$compression": []}
            else:
                with open(config_path, 'r') as file:
                    config_data = json.load(file)

            filename = self._generate_unique_filename()
            config_data["$compression"].append(filename)

            with open(config_path, 'w') as file:
                json.dump(config_data, file, indent=4)
        except Exception as e:
            self.logger.error(f"Error updating config file: {e}")

    def _cleanup_old_files(self):
        try:
            compression_folder_path = os.path.join(os.getcwd(), self.compression_folder)
            files_in_compression_folder = os.listdir(compression_folder_path)

            if len(files_in_compression_folder) > 10: 
                oldest_files = sorted(files_in_compression_folder, key=lambda x: os.path.getmtime(os.path.join(compression_folder_path, x)))
                for file in oldest_files[:-10]: 
                    file_path = os.path.join(compression_folder_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    else:
                        self.logger.warning(f"File {file_path} does not exist.")
        except Exception as e:
            self.logger.error(f"Error cleaning up old files: {e}")
