# apps/users/auth_urls.py
from django.urls import path
from .views import LoginView, MeAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

class RefreshCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("pgf_refresh")

        if not refresh_token:
            return Response({"detail": "No refresh token found"}, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token
        except Exception:
            return Response({"detail": "Invalid refresh token"}, status=401)

        res = Response({"access": str(access)})

        secure = not settings.DEBUG

        res.set_cookie(
            "pgf_access",
            str(access),
            httponly=True,
            samesite="Lax",
            secure=secure,
            path="/",
            max_age=3600,
        )

        return res


from .views import (
    PasswordResetRequestView, PasswordResetConfirmView,
    ChangePasswordView, AdminChangePasswordView
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshCookieView.as_view(), name="refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
