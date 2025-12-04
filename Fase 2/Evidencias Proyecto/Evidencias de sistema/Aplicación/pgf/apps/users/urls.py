# apps/users/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, ProfileViewSet, AdminChangePasswordView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')         # /api/v1/users/
router.register(r'profiles', ProfileViewSet, basename='profiles')

urlpatterns = router.urls + [
    path('<str:user_id>/change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),
]
# /api/v1/users/profiles/
# /api/v1/users/<id>/change-password/