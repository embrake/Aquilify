import os
import asyncio
import mimetypes

class FileStorage:
    def __init__(self, filename, content_type, data):
        self.filename = filename
        self.content_type = content_type
        self.data = data

    @property
    def content_length(self):
        return len(self.data)

    @property
    def mimetype(self):
        return self.content_type

    @property
    def name(self):
        return self.filename

    @classmethod
    async def create(cls, filename, content_type, data):
        return cls(filename, content_type, data)

    async def save(self, directory, overwrite=False):
        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        file_path = os.path.join(directory, self.filename)
        if not overwrite:
            # If the file already exists, add a suffix to the filename to make it unique
            file_name, file_extension = os.path.splitext(self.filename)
            count = 1
            while os.path.exists(file_path):
                new_filename = f"{file_name}_{count}{file_extension}"
                file_path = os.path.join(directory, new_filename)
                count += 1

        with open(file_path, 'wb') as f:
            f.write(self.data)

        return file_path  # Return the file path where the file is saved

    def get_extension(self):
        _, extension = os.path.splitext(self.filename)
        return extension

    def is_image(self):
        return self.mimetype.startswith('image/')

    def is_text(self):
        return self.mimetype.startswith('text/')

    def guess_extension(self):
        return mimetypes.guess_extension(self.mimetype)

    def guess_type(self):
        return mimetypes.guess_type(self.filename)