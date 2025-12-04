# apps/users/management/commands/listar_usuarios.py
"""
Comando para listar todos los usuarios del sistema con sus credenciales.

Este comando muestra:
- Username
- Email
- Rol
- Contraseña (si está disponible en los datos de seed)
- Estado (activo/inactivo)

Uso:
    python manage.py listar_usuarios
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

# Contraseñas conocidas de los seed data
PASSWORDS_KNOWN = {
    "admin": "admin123",
    "ejecutivo": "ejecutivo123",
    "guardia": "guardia123",
    "mecanico1": "mecanico123",
    "mecanico2": "mecanico123",
    "supervisor": "supervisor123",
    "jefe_taller": "jefe123",
    "sponsor": "sponsor123",
    "coordinador": "coord123",
    "bodega": "bodega123",
}


class Command(BaseCommand):
    help = "Lista todos los usuarios del sistema con sus credenciales"

    def handle(self, *args, **options):
        usuarios = User.objects.all().order_by('username')
        
        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("No hay usuarios en el sistema."))
            return
        
        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS("LISTA DE USUARIOS DEL SISTEMA"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))
        
        for usuario in usuarios:
            estado = "✓ ACTIVO" if usuario.is_active else "✗ INACTIVO"
            estado_style = self.style.SUCCESS if usuario.is_active else self.style.ERROR
            
            self.stdout.write(f"\n{self.style.SUCCESS(f'Usuario: {usuario.username}')}")
            self.stdout.write(f"  Email: {usuario.email or 'N/A'}")
            self.stdout.write(f"  Rol: {self.style.WARNING(usuario.rol)}")
            self.stdout.write(f"  Nombre: {usuario.get_full_name() or 'N/A'}")
            self.stdout.write(f"  Estado: {estado_style(estado)}")
            
            # Mostrar contraseña si está en la lista de conocidas
            password = PASSWORDS_KNOWN.get(usuario.username)
            if password:
                self.stdout.write(f"  {self.style.SUCCESS(f'Contraseña: {password}')}")
            else:
                self.stdout.write(f"  {self.style.WARNING('Contraseña: Desconocida (no está en seed data)')}")
            
            if usuario.rut:
                self.stdout.write(f"  RUT: {usuario.rut}")
            
            self.stdout.write(f"  Fecha de registro: {usuario.date_joined.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.stdout.write(f"\n{self.style.SUCCESS('='*80)}")
        self.stdout.write(self.style.SUCCESS(f"Total de usuarios: {usuarios.count()}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))

