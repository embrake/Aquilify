from typing import Dict
from aquilify.wrappers import Request
from aquilify.security.crypter import checkpw
from aquilify.responses import JsonResponse
from aquilify.wrappers.reqparser import Reqparser, ReqparserError
from . import db

async def nosqlupdateview(request: Request, parser: Reqparser) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({"response": f"{request.method} Method isn't supported!", "status": 405})

    parser.add_argument('email')
    parser.add_argument('password')
    parser.add_argument('up_name')

    try:
        data: Dict[str, str] = await parser.parse(request)
        email, password, updated_name = data.get('email'), data.get('password'), data.get('up_name')

        user = await db.collection.find_one({'email': email})

        if not user:
            return JsonResponse({'response': f"Email {email} isn't registered with us!"})

        if not checkpw(user.get('password'), password):
            return JsonResponse({'response': "Invalid password. Please try again!"})

        update_query = {"$set": {"name": updated_name}}
        update_result = await db.collection.update_one({"_id": user.get('_id')}, update_query)

        if update_result:
            return JsonResponse({"response": "Your name has been successfully updated!"})
        else:
            return JsonResponse({'response': "Failed to update the name."})

    except ReqparserError as e:
        return JsonResponse({'error': str(e)})

    except Exception as exe:
        return JsonResponse({'error': f"An error occurred: {str(exe)}"})
