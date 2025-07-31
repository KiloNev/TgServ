import aiohttp
import logging

logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.StreamHandler()
            ]
)

async def fetch_session_csrf_token(roblosecurity_cookie):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://auth.roblox.com/v2/logout",
                headers={'Cookie': f'.ROBLOSECURITY={roblosecurity_cookie}'}
            ) as response:
                if response.status == 403:
                    csrf_token = response.headers.get("x-csrf-token")
                    if csrf_token:
                        return csrf_token
                    else:
                        return None
                else:
                    return None
    except aiohttp.ClientError:
        return None

async def generate_auth_ticket(roblosecurity_cookie):
    try:
        csrf_token = await fetch_session_csrf_token(roblosecurity_cookie)
        if not csrf_token:
            return "Failed to fetch auth ticket"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://auth.roblox.com/v1/authentication-ticket",
                headers={
                    "x-csrf-token": csrf_token,
                    "referer": "https://www.roblox.com/madebySynaptrixBitch",
                    'Content-Type': 'application/json',
                    'Cookie': f'.ROBLOSECURITY={roblosecurity_cookie}'
                }
            ) as response:
                return {
                    "Auth_ticket": response.headers.get('rbx-authentication-ticket', "Failed to fetch auth ticket"),
                    "Csrf_token": csrf_token
                    }
    except aiohttp.ClientError:
        return "Failed to fetch auth ticket"
    
async def kill_cookie(roblosecurity_cookie, csrf_token):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://auth.roblox.com/v2/logout",
                headers={
                    "x-csrf-token": csrf_token,
                    'Cookie': f'.ROBLOSECURITY={roblosecurity_cookie}'
                    }
            ) as response:
                if response.status == 200:
                    return "Old cookie successfully killed"
                else:
                    return "Failed to kill cookie"
    except aiohttp.ClientError:
        return "Failed to kill old cookie"

async def redeem_auth_ticket(auth_ticket):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://auth.roblox.com/v1/authentication-ticket/redeem",
                json={"authenticationTicket": auth_ticket["Auth_ticket"]},
                headers={'RBXAuthenticationNegotiation': '1'}
            ) as response:
                refreshed_cookie_data = response.cookies.get('.ROBLOSECURITY', "")

                if response.status != 200:
                    return {
                        "success": False,
                        "roblox_debug_response": response.status
                    }
                
                return {
                    "success": True,
                    "refreshed_cookie": refreshed_cookie_data.value if refreshed_cookie_data else None
                }
    except aiohttp.ClientError:
        return "Failed to redeem auth ticket"