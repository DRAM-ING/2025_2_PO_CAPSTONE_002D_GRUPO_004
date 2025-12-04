"""
Comando de gestión para verificar/corregir el usuario coordinador.

Uso:
    python manage.py fix_coordinador
    python manage.py fix_coordinador --password coordinador123
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Verifica y corrige el usuario coordinador"

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='coord123',
            help='Contraseña a establecer (por defecto: coord123)',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='coordinador',
            help='Nombre de usuario (por defecto: coordinador)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"Usuario '{username}' encontrado.")
            
            # Verificar si la contraseña actual funciona
            if user.check_password(password):
                self.stdout.write(
                    self.style.SUCCESS(f"✓ La contraseña '{password}' ya es correcta.")
                )
            else:
                # Actualizar contraseña
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Contraseña actualizada a '{password}'.")
                )
            
            # Verificar que el usuario esté activo
            if not user.is_active:
                user.is_active = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS("✓ Usuario activado.")
                )
            else:
                self.stdout.write("✓ Usuario está activo.")
            
            # Verificar rol
            if user.rol != "COORDINADOR_ZONA":
                user.rol = "COORDINADOR_ZONA"
                user.save()
                self.stdout.write(
                    self.style.SUCCESS("✓ Rol actualizado a COORDINADOR_ZONA.")
                )
            else:
                self.stdout.write("✓ Rol correcto (COORDINADOR_ZONA).")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Usuario '{username}' listo para usar.\n"
                    f"  Usuario: {username}\n"
                    f"  Contraseña: {password}\n"
                    f"  Rol: {user.rol}\n"
                    f"  Activo: {user.is_active}"
                )
            )
            
        except User.DoesNotExist:
            # Crear usuario si no existe
            self.stdout.write(f"Usuario '{username}' no encontrado. Creando...")
            user = User.objects.create_user(
                username=username,
                email=f"{username}@pgf.com",
                password=password,
                rol="COORDINADOR_ZONA",
                first_name="Coordinador",
                last_name="Zona",
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Usuario '{username}' creado exitosamente.\n"
                    f"  Usuario: {username}\n"
                    f"  Contraseña: {password}\n"
                    f"  Rol: COORDINADOR_ZONA"
                )
            )

