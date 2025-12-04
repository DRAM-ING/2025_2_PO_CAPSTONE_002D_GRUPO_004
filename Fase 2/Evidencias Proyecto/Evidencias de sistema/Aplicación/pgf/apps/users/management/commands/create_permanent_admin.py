from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Crea o actualiza un usuario admin permanente con credenciales admin/admin123"

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin123'

        try:
            # Intentar obtener el usuario existente
            user = User.objects.get(username=username)
            
            # Actualizar credenciales y marcar como permanente
            user.set_password(password)
            user.email = email
            user.rol = User.Rol.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.is_permanent = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Usuario "{username}" actualizado y marcado como permanente.\n'
                    f'   Credenciales: {username} / {password}\n'
                    f'   Email: {email}\n'
                    f'   Rol: {User.Rol.ADMIN}\n'
                    f'   Este usuario no se puede eliminar, solo editar y ver.'
                )
            )
        except User.DoesNotExist:
            # Crear nuevo usuario admin permanente
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=User.Rol.ADMIN,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            # Marcar como permanente después de crear
            user.is_permanent = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Usuario admin permanente "{username}" creado exitosamente.\n'
                    f'   Credenciales: {username} / {password}\n'
                    f'   Email: {email}\n'
                    f'   Rol: {User.Rol.ADMIN}\n'
                    f'   Este usuario no se puede eliminar, solo editar y ver.'
                )
            )

