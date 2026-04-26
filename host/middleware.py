import time
from django.utils.deprecation import MiddlewareMixin

class HostMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response["X-Request-Duration-ms"] = f"{duration_ms:.2f}"
        print(f"{request.method} {request.path} {duration_ms:.2f}ms")
        return response