import requests
from requests.exceptions import HTTPError, RequestException
from django.http import HttpResponseForbidden
from json.decoder import JSONDecodeError
from django.views.debug import technical_500_response

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404 and getattr(request, 'is_debug_request', False):
            return technical_500_response(request, *sys.exc_info(), status_code=404)
        return response


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_ip(ip):
    try:
        response = requests.get(f'http://check.getipintel.net/check.php?ip={ip}&flags=m&format=json')
        response.raise_for_status()
        result = response.json()
        if 'status' in result and result['status'] == 'success':
            return float(result.get('result', 0)) > 0.95
        return False
    except JSONDecodeError:
        print("Erro ao decodificar JSON.")
        return False
    except (HTTPError, RequestException) as e:
        print(f"Erro ao fazer a requisição: {e}")
        return False

class BlockVPNMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = get_client_ip(request)
        if check_ip(client_ip):
            # Se for VPN/Proxy, retorne uma resposta proibida ou redirecione para outra página
            return HttpResponseForbidden("VPNs or Proxies are not allowed")
        response = self.get_response(request)
        return response


class RemoveCOOPHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.pop('Cross-Origin-Opener-Policy', None)
        return response
