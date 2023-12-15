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

        response = self.get_response(request)
        self.set_response_headers(request, response)
        return response

    def process_request(self, request):
        ip = self.get_client_ip(request)
        if (len(request.body) > 1e6 or
            settings.DEBUG or
            request.path in ['/login/', '/register/'] and cache.get(f"attempt_{ip}", 0) > 5 or
            cache.get(f"block_{ip}") or
            request.path.startswith('/api/') and cache.get(f"api_rate_{ip}", 0) > 10 or
            ip in self.BLOCKED_IPS or
            'file' in request.FILES and request.FILES['file'].content_type not in ['image/jpeg', 'image/png'] or
            request.headers.get('Host') not in ['localhost', 'www.mywebsite.com'] or
            'user_id' in request.GET and not request.user.is_superuser or
            request.method == 'POST' and get_token(request) != request.POST.get('csrfmiddlewaretoken') or
            request.GET.get('url') and 'localhost' in request.GET.get('url') or
                'X-Potential-Attack' in request.headers and cache.get(f"special_rate_{ip}", 0) > 3):
            return HttpResponseForbidden()

        cache.incr(f"attempt_{ip}", 1, 60)
        if request.path.startswith('/api/'):
            cache.incr(f"api_rate_{ip}", 1, 1)
        if 'X-Potential-Attack' in request.headers:
            cache.incr(f"special_rate_{ip}", 1, 1)

    def set_response_headers(self, request, response):
        headers = {
            'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'self'",
            'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
            'Referrer-Policy': 'no-referrer-when-downgrade',
            'X-XSS-Protection': '1; mode=block',
            'Feature-Policy': "microphone 'none'; camera 'none'"
        }
        for k, v in headers.items():
            response[k] = v

        if request.scheme == 'https':
            response.set_cookie('Secure', 'True', secure=True, httponly=True)
        else:
            response.set_cookie('HttpOnly', 'True', httponly=True)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
