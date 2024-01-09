from typing import (
    Dict,
    Union
)

from aquilify.wrappers import Request
from aquilify.security.crypter import checkpw
from aquilify.responses import JsonResponse
from aquilify.orm import LocalSessionManager
from aquilify.wrappers.reqparser import Reqparser, ReqparserError

import models
    
async def updateview(request: Request, parser: Reqparser) -> JsonResponse:
    if request.method == 'POST':
        
        parser.add_argument('email')
        parser.add_argument('password')
        parser.add_argument('up_name')
        
        try:
            data: Dict[Union[str, str, str]] = await parser.parse(request)
            
            with LocalSessionManager() as session:
                
                if not session.exists(models.User.email == data.get('email')):
                    return JsonResponse({'response': "Email {} isn't resgisterd with us!".format(data.get('email'))})
                
                user = session.select(models.User.email == data.get('email'))
                
                if not user or not checkpw(user[0]['password'], data.get('password')):
                    return JsonResponse({'response': "Invalid password. Please try again!"})
                
                session.update(models.User.ssid == user[0]['ssid'], models.User( name = data.get('up_name')) )
                
                return JsonResponse({"response": "Your name has been successfully updated!"})
                
        except ReqparserError as e:
            return JsonResponse({'error': str(e)})
        
        except Exception as exe:
            return JsonResponse({'error': str(exe)})
        
    return JsonResponse({
        "response": f"{request.method} Method isn't supported!",
        "status": 405
    })