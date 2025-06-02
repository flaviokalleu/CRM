from django.utils.deprecation import MiddlewareMixin

class CustomDebugMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Seu código de middleware aqui
        response = self.get_response(request)
        return response
    
