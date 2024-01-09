from typing import (
    Dict,
    Union
)

from aquilify.utils.eid import eid
from aquilify.wrappers import Request
from aquilify.responses import JsonResponse
from aquilify.orm import LocalSessionManager
from aquilify.security.crypter import hashpw
from aquilify.decorators.http import require_http_method
from aquilify.wrappers.reqparser import Reqparser, ReqparserError
from aquilify.core.backend.validator import Schema, fields, FieldValidationError

import models

class UserRegistration(Schema):
    name: str = fields.String(required=True, max_length=50)
    email: str = fields.Email(required=True)
    password: str = fields.Password(required=True, min_length=8)

async def create_user(data: Dict[str, str]) -> Union[JsonResponse, None]:
    try:
        password_hash = hashpw(data.get('password'))
        ssid = eid.random(11)

        with LocalSessionManager() as session:
            if not session.exists(models.User.email == data.get('email')):
                user = models.User(
                    ssid=ssid,
                    name=data.get('name'),
                    email=data.get('email'),
                    password=password_hash
                )
                query = session.insert(user)

                if not query:
                    return JsonResponse({"response": "Internal server error! ERR::9511:DB_SQLITE3::"})

                return JsonResponse({
                    "response": f"Congrats! {data.get('name')}, your account has been successfully created!",
                    "ssid": ssid,
                    "status": "Active"
                })
            return JsonResponse(
                {
                    'response': "User with the email {} already exists.".format(data.get('email'))
                }
            )

    except FieldValidationError as fex:
        return fex.json
    except Exception as e:
        return JsonResponse({"error": str(e)})

@require_http_method(["GET", "POST"])
async def insertview(request: Request, parser: Reqparser) -> JsonResponse:
    if request.method == 'POST':
        parser.add_argument('name', required=True, location='json', type=str)
        parser.add_argument('email', required=True, location='json', type=str)
        parser.add_argument('password', required=True, location='json', type=str)

        try:
            parsed_data: Dict[str, str] = await UserRegistration().loads(await parser.parse(request))
            response = await create_user(parsed_data)
            return response

        except (ReqparserError, FieldValidationError) as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({
        "response": f"{request.method} Method isn't supported!",
        "status": 405
    })
