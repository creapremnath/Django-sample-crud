from django.conf import settings
from django.http import HttpResponse

class AllowLocalhost5173Middleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.origin = getattr(settings, "CORS_ALLOWED_ORIGIN", "")

    def __call__(self, request):
        # Handle preflight
        if request.method == "OPTIONS":
            resp = HttpResponse()
        else:
            resp = self.get_response(request)

        if self.origin:
            request_origin = request.headers.get("Origin")
            if request_origin == self.origin:
                resp["Access-Control-Allow-Origin"] = request_origin
                resp["Vary"] = "Origin"
                resp["Access-Control-Allow-Credentials"] = "true"
                resp["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
                resp["Access-Control-Allow-Headers"] = "Content-Type"
        return resp