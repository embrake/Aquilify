import email
from io import BytesIO

class FormParser:
    def __init__(self, request):
        self.request = request

    async def parse(self):
        content_type = await self.request.header('content-type', '')

        if 'multipart/form-data' in content_type:
            boundary = content_type.split('boundary=')[-1]
            form_data = await self.parse_multipart_form_data(boundary)
        else:
            form_data = await self.parse_url_encoded_form_data()

        return form_data

    async def parse_multipart_form_data(self, boundary):
        form_data = {}
        body = await self.request.body()
        message = email.message_from_bytes(body, _class=email.parser.BytesParser)
        for part in message.walk():
            if part.is_multipart():
                continue
            content_disposition = part.get("Content-Disposition")
            if content_disposition:
                _, params = email.header.decode_header(content_disposition)
                for param, value in params:
                    if param.lower() == 'name':
                        field_name = value
                        if field_name not in form_data:
                            form_data[field_name] = []
                    if param.lower() == 'filename':
                        filename = value
                        field_data = {'filename': filename, 'content': part.get_payload(decode=True)}
                        form_data[field_name].append(field_data)
            else:
                continue

        return form_data

    async def parse_url_encoded_form_data(self):
        body = await self.request.body()
        form_data = {}
        data = body.decode('utf-8')
        form_fields = data.split('&')
        for field in form_fields:
            key, value = field.split('=')
            key = key.replace("+", " ")
            value = value.replace("+", " ")
            form_data[key] = value
        return form_data
