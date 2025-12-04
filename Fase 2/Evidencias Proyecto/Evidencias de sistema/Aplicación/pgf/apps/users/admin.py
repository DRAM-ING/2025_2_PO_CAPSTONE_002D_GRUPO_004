from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, Profile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "rol", "is_active", "is_staff", "is_permanent")
    search_fields = ("username", "email")
    list_filter = ("rol", "is_active", "is_staff", "is_permanent")
    ordering = ("id",)
    readonly_fields = ("is_permanent",)  # Solo lectura en admin para prevenir cambios accidentales

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "first_name", "last_name")
    search_fields = ("user__username", "user__email", "first_name", "last_name")
