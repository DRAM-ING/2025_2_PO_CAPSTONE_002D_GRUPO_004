"""
Comando de gestión para crear un usuario de prueba con rol BODEGA.

Uso:
    python manage.py create_bodega
    python manage.py create_bodega --username bodega --email bodega@test.com
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Profile
import secrets
import string

User = get_user_model()


class Command(BaseCommand):
    help = "Crea un usuario de prueba con rol BODEGA para gestionar inventario"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="bodega",
            help="Nombre de usuario (default: bodega)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="bodega@test.com",
            help="Email del usuario (default: bodega@test.com)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Contraseña (si no se proporciona, se genera una aleatoria)",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="Encargado",
            help="Nombre (default: Encargado)",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="de Bodega",
            help="Apellido (default: de Bodega)",
        )
        parser.add_argument(
            "--rut",
            type=str,
            default="12345678-9",
            help="RUT del usuario (default: 12345678-9)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        first_name = options["first_name"]
        last_name = options["last_name"]
        rut = options["rut"]

        # Generar contraseña si no se proporciona
        if not password:
            password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(password_chars) for _ in range(12))
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Contraseña generada automáticamente: {password}"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Guarda esta contraseña, no se mostrará nuevamente."
                )
            )

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(f"⚠️  El usuario '{username}' ya existe.")
            )
            
            # Actualizar datos
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.rol = "BODEGA"
            user.rut = rut
            user.is_active = True
            user.set_password(password)
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Usuario '{username}' actualizado con rol BODEGA")
            )
        else:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                rol="BODEGA",
                rut=rut,
                is_active=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ Usuario '{username}' creado con rol BODEGA")
            )

        # Crear o actualizar perfil
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "notificaciones_email": True,
                "notificaciones_sonido": True,
            }
        )
        
        if not created:
            profile.first_name = first_name
            profile.last_name = last_name
            profile.save()

        # Mostrar información del usuario
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("📦 USUARIO BODEGA CREADO"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Username: {user.username}")
        self.stdout.write(f"Email: {user.email}")
        self.stdout.write(f"Nombre: {user.get_full_name()}")
        self.stdout.write(f"RUT: {user.rut}")
        self.stdout.write(f"Rol: {user.rol}")
        self.stdout.write(f"Contraseña: {password}")
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Usuario listo para probar el módulo de inventario!"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  Puedes iniciar sesión con estas credenciales en el frontend."
            )
        )

