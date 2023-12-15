import re
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.middleware.csrf import get_token


class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response
        return self.get_response(request)

    def process_request(self, request):

        # 1. Clickjacking protection
        response.headers['X-Frame-Options'] = 'DENY'

        # 2. Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'"

        # 3. Cookie Security
        if request.scheme == 'https':
            request.cookies['Secure'] = True
        request.cookies['HttpOnly'] = True

        # 4. HSTS Preload
        request.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'

        # 5. Request size limitation
        max_request_size = 1e6  # 1MB
        if len(request.body) > max_request_size:
            return HttpResponseForbidden("Request size too large")

        # 6. Referrer Policy
        request.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'

        # 7. Check for DEBUG in production
        if request.settings.DEBUG:
            return JsonResponse({"error": "DEBUG mode should not be enabled in production!"}, status=500)

        # 8. Brute force protection on specific endpoints
        if request.path in ['/login/', '/register/']:
            ip = self.get_client_ip(request)
            if cache.get(f"attempt_{ip}"):
                cache.incr(f"attempt_{ip}")
            else:
                cache.set(f"attempt_{ip}", 1, 60)  # 1 min
            if cache.get(f"attempt_{ip}") > 5:
                return HttpResponseForbidden("Too many attempts. Please wait.")

        # 9. IP block for suspicious behavior
        if cache.get(f"block_{ip}"):
            return HttpResponseForbidden("You've been temporarily blocked due to suspicious behavior.")

        # 10. Rate limiting based on endpoint
        if request.path.startswith('/api/'):
            if cache.get(f"api_rate_{ip}"):
                cache.incr(f"api_rate_{ip}")
            else:
                cache.set(f"api_rate_{ip}", 1, 1)  # 1 second
            if cache.get(f"api_rate_{ip}") > 10:
                return HttpResponseForbidden("Too many requests. Slow down.")

        # 11. Lista de IPs Bloqueados
        ip = self.get_client_ip(request)
        if ip in self.BLOCKED_IPS:
            return HttpResponseForbidden("Blocked IP address")

        # 12. Verificação de MIME Type (para uploads de arquivos)
        if 'file' in request.FILES:
            # Just an example
            if request.FILES['file'].content_type not in ['image/jpeg', 'image/png']:
                return HttpResponseForbidden("Unsupported file type")

        # 13. Verificação do Cabeçalho Host
        allowed_hosts = ['mywebsite.com', 'www.mywebsite.com']
        if request.headers.get('Host') not in allowed_hosts:
            return HttpResponseForbidden("Invalid Host header")

        # 14. Proteção XSS
        request.headers['X-XSS-Protection'] = '1; mode=block'

        # 15. Política de Feature
        request.headers['Feature-Policy'] = "microphone 'none'; camera 'none'"

        # 16. Prevenção contra manipulação de parâmetros (apenas um exemplo)
        if 'user_id' in request.GET and not request.user.is_superuser:
            return HttpResponseForbidden("Parameter tampering detected")

        # 17. Verificação do Token CSRF para POST requests
        if request.method == 'POST' and get_token(request) != request.POST.get('csrfmiddlewaretoken'):
            return HttpResponseForbidden("Invalid CSRF token")

        # 18. Evitar vazamento de informações através de erros
        if settings.DEBUG is False:
            request.META['wsgi.errors'] = None

        # 19. Verificação SSRF (Apenas um exemplo básico)
        url = request.GET.get('url')
        if url and 'localhost' in url:
            return HttpResponseForbidden("Potential SSRF detected")

        # 20. Limitação de taxa baseada em cabeçalhos (Exemplo Básico)
        if 'X-Potential-Attack' in request.headers:
            if cache.get(f"special_rate_{ip}"):
                cache.incr(f"special_rate_{ip}")
            else:
                cache.set(f"special_rate_{ip}", 1, 1)  # 1 second
            if cache.get(f"special_rate_{ip}") > 3:
                return HttpResponseForbidden("Too many requests. Slow down.")

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
