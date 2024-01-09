from aquilify.wrappers import Request
from aquilify.wrappers.reqparser import ReqparserError, Reqparser
from aquilify.responses import JsonResponse
from aquilify.core.backend.validator import Schema, fields, FieldValidationError
from aquilify.utils.eid import eid
from aquilify.security import crypter

from . import db

import typing

class UserRegistration(Schema):
    name: str = fields.String(required=True, max_length=50)
    email: str = fields.Email(required=True)
    password: str = fields.Password(required=True, min_length=8)
    
async def create_user(data: typing.Dict[str, str]) -> typing.Union[JsonResponse, None]:
    try:
        password_hash = crypter.hashpw(data.get('password'))
        ssid = eid.random(11)

        if not await db.collection.find_one( { "email": data.get('email') } ):
            
            query = await db.collection.insert_one(
                {
                    "id": "auto_inc",
                    "ssid": ssid,
                    "name": data.get('name'),
                    "email": data.get('email'),
                    "password": password_hash
                }
            )

            if not query:
                return JsonResponse({"response": "Internal server error! ERR::9512:NOSQL_ERR::"})

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
    
async def nosqlisertview(request: Request, parser: Reqparser) -> JsonResponse:
    if request.method == 'POST':
        parser.add_argument('name', required=True, location='json', type=str)
        parser.add_argument('email', required=True, location='json', type=str)
        parser.add_argument('password', required=True, location='json', type=str)

        try:
            parsed_data: typing.Dict[str, str] = await UserRegistration().loads(await parser.parse(request))
            response = await create_user(parsed_data)
            return response

        except (ReqparserError, FieldValidationError) as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({
        "response": f"{request.method} Method isn't supported!",
        "status": 405
    })