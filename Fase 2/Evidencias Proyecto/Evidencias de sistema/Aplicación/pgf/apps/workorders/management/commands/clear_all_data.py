# apps/workorders/management/commands/clear_all_data.py
"""
Comando de gestión para limpiar todos los datos de la aplicación.

Este comando borra todos los datos de las tablas principales:
- Órdenes de Trabajo y relacionados (ItemOT, Presupuesto, Pausa, Evidencia, etc.)
- Vehículos e Ingresos
- Usuarios (excepto el usuario actual si se especifica)
- Choferes
- Emergencias
- Notificaciones
- Inventario
- Agenda

Uso:
    python manage.py clear_all_data
    python manage.py clear_all_data --keep-users  # Mantiene todos los usuarios
    python manage.py clear_all_data --keep-current-user  # Mantiene el usuario actual
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings

# Importar todos los modelos
from apps.workorders.models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup, 
    Aprobacion, Pausa, Checklist, Evidencia, ComentarioOT, Auditoria,
    BloqueoVehiculo, VersionEvidencia
)
from apps.vehicles.models import Vehiculo, IngresoVehiculo, EvidenciaIngreso, HistorialVehiculo, BackupVehiculo
from apps.users.models import Profile, PasswordResetToken
from apps.drivers.models import Chofer, HistorialAsignacionVehiculo
from apps.emergencies.models import EmergenciaRuta
from apps.notifications.models import Notification
from apps.inventory.models import Repuesto, Stock

# Intentar importar scheduling si existe
try:
    from apps.scheduling.models import Agenda
    HAS_SCHEDULING = True
except ImportError:
    HAS_SCHEDULING = False

User = get_user_model()


class Command(BaseCommand):
    help = 'Limpia todos los datos de la aplicación (tablas principales)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Mantiene todos los usuarios (solo borra sus relaciones)',
        )
        parser.add_argument(
            '--keep-current-user',
            action='store_true',
            help='Mantiene el usuario actual (requiere --username)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username del usuario a mantener (requerido con --keep-current-user)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma la eliminación sin preguntar',
        )

    def handle(self, *args, **options):
        keep_users = options['keep_users']
        keep_current_user = options['keep_current_user']
        username = options.get('username')
        confirm = options['confirm']

        if keep_current_user and not username:
            self.stdout.write(
                self.style.ERROR('Error: --username es requerido cuando se usa --keep-current-user')
            )
            return

        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  ADVERTENCIA: Este comando borrará TODOS los datos de la aplicación.\n'
                    'Esto incluye:\n'
                    '  - Todas las Órdenes de Trabajo\n'
                    '  - Todos los Vehículos e Ingresos\n'
                    '  - Todos los Usuarios (a menos que uses --keep-users o --keep-current-user)\n'
                    '  - Todos los Choferes\n'
                    '  - Todas las Emergencias\n'
                    '  - Todas las Notificaciones\n'
                    '  - Todo el Inventario\n'
                    '  - Toda la Agenda\n'
                )
            )
            
            if keep_users:
                self.stdout.write(self.style.WARNING('  → Se mantendrán todos los usuarios'))
            if keep_current_user:
                self.stdout.write(self.style.WARNING(f'  → Se mantendrá el usuario: {username}'))
            
            respuesta = input('\n¿Estás seguro de que deseas continuar? (escribe "SI" para confirmar): ')
            if respuesta.upper() != 'SI':
                self.stdout.write(self.style.SUCCESS('Operación cancelada.'))
                return

        # Usuario a mantener (si se especifica)
        user_to_keep = None
        if keep_current_user:
            try:
                user_to_keep = User.objects.get(username=username)
                self.stdout.write(self.style.SUCCESS(f'✓ Usuario a mantener: {user_to_keep.username}'))
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Error: Usuario "{username}" no encontrado')
                )
                return

        self.stdout.write(self.style.WARNING('\n🗑️  Iniciando limpieza de datos...\n'))

        try:
            with transaction.atomic():
                # 1. Borrar datos relacionados con Órdenes de Trabajo (en orden de dependencias)
                self.stdout.write('  → Borrando Evidencias...')
                count = Evidencia.objects.all().count()
                Evidencia.objects.all().delete()
                self.stdout.write(f'    ✓ {count} evidencias eliminadas')

                self.stdout.write('  → Borrando Comentarios de OT...')
                count = ComentarioOT.objects.all().count()
                ComentarioOT.objects.all().delete()
                self.stdout.write(f'    ✓ {count} comentarios eliminados')

                self.stdout.write('  → Borrando Checklists...')
                count = Checklist.objects.all().count()
                Checklist.objects.all().delete()
                self.stdout.write(f'    ✓ {count} checklists eliminados')

                self.stdout.write('  → Borrando Pausas...')
                count = Pausa.objects.all().count()
                Pausa.objects.all().delete()
                self.stdout.write(f'    ✓ {count} pausas eliminadas')

                self.stdout.write('  → Borrando Detalles de Presupuesto...')
                count = DetallePresup.objects.all().count()
                DetallePresup.objects.all().delete()
                self.stdout.write(f'    ✓ {count} detalles de presupuesto eliminados')

                self.stdout.write('  → Borrando Aprobaciones...')
                count = Aprobacion.objects.all().count()
                Aprobacion.objects.all().delete()
                self.stdout.write(f'    ✓ {count} aprobaciones eliminadas')

                self.stdout.write('  → Borrando Presupuestos...')
                count = Presupuesto.objects.all().count()
                Presupuesto.objects.all().delete()
                self.stdout.write(f'    ✓ {count} presupuestos eliminados')

                self.stdout.write('  → Borrando Items de OT...')
                count = ItemOT.objects.all().count()
                ItemOT.objects.all().delete()
                self.stdout.write(f'    ✓ {count} items eliminados')

                self.stdout.write('  → Borrando Órdenes de Trabajo...')
                count = OrdenTrabajo.objects.all().count()
                OrdenTrabajo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} órdenes de trabajo eliminadas')

                self.stdout.write('  → Borrando Auditorías...')
                count = Auditoria.objects.all().count()
                Auditoria.objects.all().delete()
                self.stdout.write(f'    ✓ {count} auditorías eliminadas')

                # 2. Borrar datos relacionados con Vehículos
                self.stdout.write('  → Borrando Versiones de Evidencias...')
                count = VersionEvidencia.objects.all().count()
                VersionEvidencia.objects.all().delete()
                self.stdout.write(f'    ✓ {count} versiones eliminadas')

                self.stdout.write('  → Borrando Bloqueos de Vehículos...')
                count = BloqueoVehiculo.objects.all().count()
                BloqueoVehiculo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} bloqueos eliminados')

                self.stdout.write('  → Borrando Evidencias de Ingreso...')
                count = EvidenciaIngreso.objects.all().count()
                EvidenciaIngreso.objects.all().delete()
                self.stdout.write(f'    ✓ {count} evidencias de ingreso eliminadas')

                self.stdout.write('  → Borrando Historial de Vehículos...')
                count = HistorialVehiculo.objects.all().count()
                HistorialVehiculo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} registros de historial eliminados')

                self.stdout.write('  → Borrando Backups de Vehículos...')
                count = BackupVehiculo.objects.all().count()
                BackupVehiculo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} backups eliminados')

                self.stdout.write('  → Borrando Ingresos de Vehículos...')
                count = IngresoVehiculo.objects.all().count()
                IngresoVehiculo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} ingresos eliminados')

                self.stdout.write('  → Borrando Vehículos...')
                count = Vehiculo.objects.all().count()
                Vehiculo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} vehículos eliminados')

                # 3. Borrar datos relacionados con Choferes
                self.stdout.write('  → Borrando Historial de Asignaciones...')
                count = HistorialAsignacionVehiculo.objects.all().count()
                HistorialAsignacionVehiculo.objects.all().delete()
                self.stdout.write(f'    ✓ {count} asignaciones eliminadas')

                self.stdout.write('  → Borrando Choferes...')
                count = Chofer.objects.all().count()
                Chofer.objects.all().delete()
                self.stdout.write(f'    ✓ {count} choferes eliminados')

                # 4. Borrar Emergencias
                self.stdout.write('  → Borrando Emergencias...')
                count = EmergenciaRuta.objects.all().count()
                EmergenciaRuta.objects.all().delete()
                self.stdout.write(f'    ✓ {count} emergencias eliminadas')

                # 5. Borrar Notificaciones
                self.stdout.write('  → Borrando Notificaciones...')
                count = Notification.objects.all().count()
                Notification.objects.all().delete()
                self.stdout.write(f'    ✓ {count} notificaciones eliminadas')

                # 6. Borrar Inventario
                self.stdout.write('  → Borrando Stock...')
                count = Stock.objects.all().count()
                Stock.objects.all().delete()
                self.stdout.write(f'    ✓ {count} registros de stock eliminados')

                self.stdout.write('  → Borrando Repuestos...')
                count = Repuesto.objects.all().count()
                Repuesto.objects.all().delete()
                self.stdout.write(f'    ✓ {count} repuestos eliminados')

                # 7. Borrar Agenda (si existe)
                if HAS_SCHEDULING:
                    from apps.scheduling.models import CupoDiario
                    self.stdout.write('  → Borrando Cupos Diarios...')
                    count = CupoDiario.objects.all().count()
                    CupoDiario.objects.all().delete()
                    self.stdout.write(f'    ✓ {count} cupos eliminados')

                    self.stdout.write('  → Borrando Agenda...')
                    count = Agenda.objects.all().count()
                    Agenda.objects.all().delete()
                    self.stdout.write(f'    ✓ {count} registros de agenda eliminados')

                # 8. Borrar Tokens de Recuperación de Contraseña
                self.stdout.write('  → Borrando Tokens de Recuperación...')
                count = PasswordResetToken.objects.all().count()
                PasswordResetToken.objects.all().delete()
                self.stdout.write(f'    ✓ {count} tokens eliminados')

                # 9. Borrar Usuarios (si no se especifica mantenerlos)
                if not keep_users:
                    if keep_current_user and user_to_keep:
                        # Borrar todos excepto el usuario actual
                        self.stdout.write(f'  → Borrando Usuarios (excepto {user_to_keep.username})...')
                        count = User.objects.exclude(id=user_to_keep.id).count()
                        # Primero borrar los perfiles asociados
                        Profile.objects.exclude(user=user_to_keep).delete()
                        # Luego borrar los usuarios
                        User.objects.exclude(id=user_to_keep.id).delete()
                        self.stdout.write(f'    ✓ {count} usuarios eliminados')
                        self.stdout.write(f'    ✓ Usuario {user_to_keep.username} mantenido')
                    else:
                        # Borrar todos los usuarios
                        self.stdout.write('  → Borrando Perfiles...')
                        count = Profile.objects.all().count()
                        Profile.objects.all().delete()
                        self.stdout.write(f'    ✓ {count} perfiles eliminados')

                        self.stdout.write('  → Borrando Usuarios...')
                        count = User.objects.all().count()
                        User.objects.all().delete()
                        self.stdout.write(f'    ✓ {count} usuarios eliminados')
                else:
                    self.stdout.write('  → Manteniendo todos los usuarios (solo se borraron relaciones)')

            self.stdout.write(self.style.SUCCESS('\n✅ Limpieza completada exitosamente!\n'))
            self.stdout.write('   Todas las tablas han sido limpiadas.')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error durante la limpieza: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            raise

