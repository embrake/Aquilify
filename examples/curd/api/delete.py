from typing import Dict
from aquilify.wrappers import Request
from aquilify.security.crypter import checkpw
from aquilify.responses import JsonResponse
from aquilify.orm import LocalSessionManager
from aquilify.wrappers.reqparser import Reqparser, ReqparserError
import models

async def deleteview(request: Request, parser: Reqparser) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({"response": f"{request.method} Method isn't supported!", "status": 405})

    parser.add_argument('email')
    parser.add_argument('password')

    try:
        request_data: Dict[str, str] = await parser.parse(request)
        email, password = request_data.get('email'), request_data.get('password')

        with LocalSessionManager() as session:
            user_exists = session.exists(models.User.email == email)
            if not user_exists:
                return JsonResponse({'response': f"Email {email} isn't registered with us!"})

            user = session.select(models.User.email == email)

            if not user or not checkpw(user[0]['password'], password):
                return JsonResponse({'response': "Invalid password. Please try again!"})

            session.delete(models.User.email == email)
            return JsonResponse({"response": "Your account has been successfully deleted."})

    except ReqparserError as e:
        return JsonResponse({'error': str(e)})

    except Exception as exe:
        return JsonResponse({'error': str(exe)})
