from typing import Dict
from aquilify.wrappers import Request
from aquilify.security.crypter import checkpw
from aquilify.responses import JsonResponse
from aquilify.wrappers.reqparser import Reqparser, ReqparserError
from . import db

async def nosqldeleteview(request: Request, parser: Reqparser) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({"response": f"{request.method} Method isn't supported!", "status": 405})

    parser.add_argument('email')
    parser.add_argument('password')

    try:
        data: Dict[str, str] = await parser.parse(request)
        email, password = data.get('email'), data.get('password')

        user = await db.collection.find_one({'email': email})

        if not user:
            return JsonResponse({'response': f"Email {email} isn't registered with us!"})

        if not checkpw(user.get('password'), password):
            return JsonResponse({'response': "Invalid password. Please try again!"})

        deletion_result = await db.collection.delete_one({'_id': user.get('_id')})

        if deletion_result:
            return JsonResponse({"response": "Your account has been successfully deleted."})
        else:
            return JsonResponse({"response": "Failed to delete the account."})

    except ReqparserError as e:
        return JsonResponse({'error': str(e)})

    except Exception as exe:
        return JsonResponse({'error': f"An error occurred: {str(exe)}"})
