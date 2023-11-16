import os
import email.parser
import mimetypes
from .filestorage import FileStorage

class FormParser:
    @staticmethod
    async def parse(body, boundary):
        form_data = {}
        parser = email.parser.BytesParser()

        parts = body.split(b'--' + boundary.encode())
        for part in parts:
            part = part.strip()
            if not part:
                continue

            msg = parser.parsebytes(part)

            if 'Content-Disposition' in msg:
                content_disposition = msg['Content-Disposition']
                field_name, file_name = FormParser.parse_content_disposition(content_disposition)

                if file_name:
                    # This is a file upload
                    file_data = {
                        'filename': file_name,
                        'content_type': msg.get_content_type(),
                        'data': msg.get_payload(decode=True)
                    }
                    form_data[field_name] = await FileStorage.create(**file_data)
                elif field_name:
                    # This is a regular form field
                    field_value = msg.get_payload(decode=True).decode('utf-8')
                    form_data[field_name] = field_value

        return form_data

    @staticmethod
    def parse_content_disposition(content_disposition):
        field_name = None
        file_name = None

        disposition_params = content_disposition.split(';')
        for param in disposition_params:
            param = param.strip()
            if param.startswith('name='):
                field_name = param.split('=')[1].strip('"')
            elif param.startswith('filename='):
                file_name = param.split('=')[1].strip('"')

        return field_name, file_name

    @staticmethod
    def parse_query_string(query_string):
        query_data = {}
        if query_string:
            query_params = query_string.split('&')
            for param in query_params:
                param = param.split('=')
                if len(param) == 2:
                    key, value = param
                    query_data[key] = value
        return query_data
    
    @staticmethod
    def parseUrlEncoded(body):
        form_data = {}
        key_value_pairs = body.split('&')
        for pair in key_value_pairs:
            key, value = pair.split('=')
            form_data[key] = value
        return form_data