from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Marca un usuario como permanente (no se puede eliminar, solo editar y ver)"

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Nombre de usuario (username) del usuario a marcar como permanente'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']

        try:
            user = User.objects.get(username=username)
            
            if user.is_permanent:
                self.stdout.write(
                    self.style.WARNING(
                        f'El usuario "{username}" ya está marcado como permanente.'
                    )
                )
                return

            user.is_permanent = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Usuario "{username}" marcado como permanente exitosamente.\n'
                    f'   Este usuario ahora solo se puede editar y ver, no eliminar.'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error: No se encontró un usuario con el username "{username}".'
                )
            )

