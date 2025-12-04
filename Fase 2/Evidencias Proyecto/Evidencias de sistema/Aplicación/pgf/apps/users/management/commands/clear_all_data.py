from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

class Command(BaseCommand):
    help = "Borra todos los datos de todas las tablas, manteniendo el admin permanente"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Ejecutar sin confirmación interactiva',
        )
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Mantener todos los usuarios (solo borrar el admin permanente si no está marcado como permanente)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Confirmar antes de borrar (a menos que se use --no-input)
        if not options['no_input']:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  ADVERTENCIA: Este comando borrará TODOS los datos de la base de datos.\n'
                '   Solo se mantendrá el usuario admin permanente (si existe).\n'
            ))
            confirm = input('¿Está seguro de que desea continuar? (escriba "SI" para confirmar): ')
            if confirm != 'SI':
                self.stdout.write(self.style.ERROR('Operación cancelada.'))
                return

        # Contar registros antes de borrar
        counts = {}
        
        # Ejecutar cada sección en su propia transacción para que si una falla,
        # las anteriores no se reviertan
        try:
                
                # ==================== BORRAR DATOS DE WORKORDERS ====================
                self.stdout.write('\n🗑️  Borrando datos de órdenes de trabajo...')
                try:
                    from apps.workorders.models import (
                        OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
                        Aprobacion, Pausa, Checklist, Evidencia, Auditoria,
                        ComentarioOT, BloqueoVehiculo, VersionEvidencia
                    )
                    
                    counts['ComentarioOT'] = ComentarioOT.objects.count()
                    ComentarioOT.objects.all().delete()
                    
                    counts['VersionEvidencia'] = VersionEvidencia.objects.count()
                    VersionEvidencia.objects.all().delete()
                    
                    counts['Evidencia'] = Evidencia.objects.count()
                    Evidencia.objects.all().delete()
                    
                    counts['Checklist'] = Checklist.objects.count()
                    Checklist.objects.all().delete()
                    
                    counts['Pausa'] = Pausa.objects.count()
                    Pausa.objects.all().delete()
                    
                    counts['Aprobacion'] = Aprobacion.objects.count()
                    Aprobacion.objects.all().delete()
                    
                    counts['DetallePresup'] = DetallePresup.objects.count()
                    DetallePresup.objects.all().delete()
                    
                    counts['Presupuesto'] = Presupuesto.objects.count()
                    Presupuesto.objects.all().delete()
                    
                    counts['ItemOT'] = ItemOT.objects.count()
                    ItemOT.objects.all().delete()
                    
                    counts['OrdenTrabajo'] = OrdenTrabajo.objects.count()
                    OrdenTrabajo.objects.all().delete()
                    
                    counts['BloqueoVehiculo'] = BloqueoVehiculo.objects.count()
                    BloqueoVehiculo.objects.all().delete()
                    
                    counts['Auditoria'] = Auditoria.objects.count()
                    Auditoria.objects.all().delete()
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Datos de workorders borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de workorders: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar workorders: {e}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))

                # ==================== BORRAR DATOS DE SCHEDULING (ANTES DE VEHICLES) ====================
                # IMPORTANTE: Agenda tiene on_delete=PROTECT en vehiculo
                # Necesitamos borrarlo ANTES de borrar vehículos
                self.stdout.write('\n🗑️  Borrando datos de programación...')
                try:
                    from apps.scheduling.models import Agenda, CupoDiario
                    
                    counts['CupoDiario'] = CupoDiario.objects.count()
                    CupoDiario.objects.all().delete()
                    
                    counts['Agenda'] = Agenda.objects.count()
                    Agenda.objects.all().delete()
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Datos de scheduling borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de scheduling: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar scheduling: {e}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))

                # ==================== BORRAR DATOS DE EMERGENCIES (ANTES DE VEHICLES) ====================
                # IMPORTANTE: EmergenciaRuta tiene on_delete=PROTECT en vehiculo
                # Necesitamos borrarlo ANTES de borrar vehículos
                self.stdout.write('\n🗑️  Borrando datos de emergencias...')
                try:
                    from apps.emergencies.models import EmergenciaRuta
                    
                    counts['EmergenciaRuta'] = EmergenciaRuta.objects.count()
                    EmergenciaRuta.objects.all().delete()
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Datos de emergencies borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de emergencies: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar emergencies: {e}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))

                # ==================== BORRAR DATOS DE INVENTORY (ANTES DE VEHICLES) ====================
                # IMPORTANTE: HistorialRepuestoVehiculo tiene relación con Vehiculo
                # Necesitamos borrarlo ANTES de borrar vehículos
                self.stdout.write('\n🗑️  Borrando datos de inventario...')
                try:
                    from apps.inventory.models import (
                        Repuesto, Stock, MovimientoStock, SolicitudRepuesto,
                        HistorialRepuestoVehiculo
                    )
                    
                    counts['HistorialRepuestoVehiculo'] = HistorialRepuestoVehiculo.objects.count()
                    HistorialRepuestoVehiculo.objects.all().delete()
                    
                    counts['MovimientoStock'] = MovimientoStock.objects.count()
                    MovimientoStock.objects.all().delete()
                    
                    counts['SolicitudRepuesto'] = SolicitudRepuesto.objects.count()
                    SolicitudRepuesto.objects.all().delete()
                    
                    counts['Stock'] = Stock.objects.count()
                    Stock.objects.all().delete()
                    
                    counts['Repuesto'] = Repuesto.objects.count()
                    Repuesto.objects.all().delete()
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Datos de inventory borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de inventory: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar inventory: {e}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))

                # ==================== BORRAR DATOS DE DRIVERS (ANTES DE VEHICLES) ====================
                # IMPORTANTE: HistorialAsignacionVehiculo tiene on_delete=PROTECT en vehiculo
                # Necesitamos borrarlo ANTES de borrar vehículos
                self.stdout.write('\n🗑️  Borrando datos de choferes...')
                try:
                    from apps.drivers.models import Chofer, HistorialAsignacionVehiculo
                    
                    # Borrar historial de asignaciones primero (tiene PROTECT)
                    counts['HistorialAsignacionVehiculo'] = HistorialAsignacionVehiculo.objects.count()
                    HistorialAsignacionVehiculo.objects.all().delete()
                    
                    # Limpiar relaciones de choferes con vehículos antes de borrar
                    counts['Chofer'] = Chofer.objects.count()
                    Chofer.objects.update(vehiculo_asignado=None)  # Limpiar relaciones primero
                    Chofer.objects.all().delete()
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Datos de drivers borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de drivers: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar drivers: {e}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))

                # ==================== BORRAR DATOS DE VEHICLES ====================
                self.stdout.write('\n🗑️  Borrando datos de vehículos...')
                with transaction.atomic():
                    try:
                        from apps.vehicles.models import (
                            Vehiculo, IngresoVehiculo, EvidenciaIngreso, HistorialVehiculo, BackupVehiculo
                        )
                        
                        counts['EvidenciaIngreso'] = EvidenciaIngreso.objects.count()
                        EvidenciaIngreso.objects.all().delete()
                        
                        counts['IngresoVehiculo'] = IngresoVehiculo.objects.count()
                        IngresoVehiculo.objects.all().delete()
                        
                        counts['HistorialVehiculo'] = HistorialVehiculo.objects.count()
                        HistorialVehiculo.objects.all().delete()
                        
                        # IMPORTANTE: BackupVehiculo tiene on_delete=PROTECT en vehiculo_principal y vehiculo_backup
                        # Necesitamos borrarlo ANTES de borrar vehículos, y limpiar relaciones primero
                        counts['BackupVehiculo'] = BackupVehiculo.objects.count()
                        # Limpiar relaciones de backups antes de borrar (por si hay alguna referencia circular)
                        BackupVehiculo.objects.update(ot=None)  # Limpiar relación con OT si existe
                        BackupVehiculo.objects.all().delete()
                        
                        # Limpiar relaciones de vehículos con choferes y supervisor antes de borrar
                        Vehiculo.objects.update(supervisor=None)  # Limpiar relación con supervisor
                        
                        # Borrar específicamente vehículos del seed_demo primero
                        patentes_seed_demo = [
                            "ABCJ12", "KLMN34", "PQRS56", "TUVW78", 
                            "XYZA90", "BCDE12", "FGHI34", "JKLM56"
                        ]
                        vehiculos_seed = Vehiculo.objects.filter(patente__in=patentes_seed_demo)
                        count_seed_vehiculos = vehiculos_seed.count()
                        if count_seed_vehiculos > 0:
                            vehiculos_seed.delete()
                            self.stdout.write(self.style.SUCCESS(f'   ✅ {count_seed_vehiculos} vehículo(s) del seed_demo borrado(s)'))
                        
                        counts['Vehiculo'] = Vehiculo.objects.count()
                        
                        if counts['Vehiculo'] > 0:
                            # Verificar si hay relaciones que impidan el borrado
                            try:
                                # Intentar borrar uno por uno para identificar problemas
                                vehiculos = list(Vehiculo.objects.all())
                                deleted_count = 0
                                for vehiculo in vehiculos:
                                    try:
                                        vehiculo.delete()
                                        deleted_count += 1
                                    except Exception as e:
                                        self.stdout.write(self.style.ERROR(
                                            f'   ❌ Error al borrar vehículo {vehiculo.patente}: {e}'
                                        ))
                                        # Intentar forzar borrado limpiando relaciones problemáticas
                                        try:
                                            # Limpiar todas las relaciones posibles
                                            vehiculo.supervisor = None
                                            vehiculo.save()
                                            vehiculo.delete()
                                            deleted_count += 1
                                        except Exception as e2:
                                            self.stdout.write(self.style.ERROR(
                                                f'   ❌ Error al forzar borrado de {vehiculo.patente}: {e2}'
                                            ))
                                
                                if deleted_count != counts['Vehiculo']:
                                    self.stdout.write(self.style.WARNING(
                                        f'   ⚠️  Se intentaron borrar {counts["Vehiculo"]} vehículos, pero solo se borraron {deleted_count}'
                                    ))
                            except Exception as e:
                                # Si falla el borrado individual, intentar borrado masivo
                                self.stdout.write(self.style.WARNING(
                                    f'   ⚠️  Error en borrado individual, intentando borrado masivo: {e}'
                                ))
                                try:
                                    deleted_count, _ = Vehiculo.objects.all().delete()
                                    if deleted_count != counts['Vehiculo']:
                                        self.stdout.write(self.style.WARNING(
                                            f'   ⚠️  Borrado masivo: se intentaron borrar {counts["Vehiculo"]} vehículos, pero solo se borraron {deleted_count}'
                                        ))
                                except Exception as e2:
                                    self.stdout.write(self.style.ERROR(
                                        f'   ❌ Error en borrado masivo de vehículos: {e2}'
                                    ))
                                    raise
                        else:
                            deleted_count = 0
                        
                        self.stdout.write(self.style.SUCCESS(f'   ✅ {deleted_count} vehículos borrados'))
                    except ImportError as e:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de vehicles: {e}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar vehicles: {e}'))
                        import traceback
                        self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))
                        raise


                # ==================== BORRAR DATOS DE NOTIFICATIONS ====================
                self.stdout.write('\n🗑️  Borrando datos de notificaciones...')
                try:
                    from apps.notifications.models import Notification
                    
                    counts['Notification'] = Notification.objects.count()
                    Notification.objects.all().delete()
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Datos de notifications borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de notifications: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar notifications: {e}'))

                # ==================== BORRAR USUARIOS (EXCEPTO ADMIN PERMANENTE) ====================
                self.stdout.write('\n🗑️  Borrando usuarios (excepto admin permanente)...')
                try:
                    # Obtener usuarios permanentes para no borrarlos
                    usuarios_permanentes = User.objects.filter(is_permanent=True)
                    count_permanentes = usuarios_permanentes.count()
                    
                    # Lista de usuarios del seed_demo que deben borrarse (excepto admin si es permanente)
                    usuarios_seed_demo = [
                        "admin", "ejecutivo", "guardia", "mecanico1", "mecanico2",
                        "supervisor", "jefe_taller", "sponsor", "coordinador", "recepcionista"
                    ]
                    
                    if options['keep_users']:
                        counts['User'] = 0
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Opción --keep-users activada, no se borraron usuarios'))
                    else:
                        # Primero, asegurarse de que los usuarios del seed_demo se borren
                        # (excepto si son permanentes)
                        usuarios_seed_a_borrar = User.objects.filter(
                            username__in=usuarios_seed_demo
                        ).exclude(is_permanent=True)
                        count_seed = usuarios_seed_a_borrar.count()
                        if count_seed > 0:
                            usuarios_seed_a_borrar.delete()
                            self.stdout.write(self.style.SUCCESS(f'   ✅ {count_seed} usuario(s) del seed_demo borrado(s)'))
                        
                        # Borrar todos los usuarios excepto los permanentes
                        usuarios_a_borrar = User.objects.exclude(is_permanent=True)
                        counts['User'] = usuarios_a_borrar.count()
                        usuarios_a_borrar.delete()
                        
                        if count_permanentes > 0:
                            self.stdout.write(self.style.SUCCESS(
                                f'   ✅ {counts["User"]} usuarios borrados, {count_permanentes} usuario(s) permanente(s) mantenido(s)'
                            ))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'   ✅ {counts["User"]} usuarios borrados'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar usuarios: {e}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'   Traceback: {traceback.format_exc()}'))

                # ==================== BORRAR PROFILES ====================
                self.stdout.write('\n🗑️  Borrando perfiles de usuarios...')
                try:
                    from apps.users.models import Profile, PasswordResetToken
                    
                    # Borrar tokens de reset de contraseña
                    counts['PasswordResetToken'] = PasswordResetToken.objects.count()
                    PasswordResetToken.objects.all().delete()
                    
                    # Borrar perfiles (excepto los de usuarios permanentes)
                    if options['keep_users']:
                        counts['Profile'] = 0
                        self.stdout.write(self.style.WARNING('   ⚠️  Opción --keep-users activada, no se borraron perfiles'))
                    else:
                        # Obtener IDs de usuarios permanentes
                        usuarios_permanentes_ids = User.objects.filter(is_permanent=True).values_list('id', flat=True)
                        profiles_a_borrar = Profile.objects.exclude(user_id__in=usuarios_permanentes_ids)
                        counts['Profile'] = profiles_a_borrar.count()
                        profiles_a_borrar.delete()
                        
                        self.stdout.write(self.style.SUCCESS(f'   ✅ {counts["Profile"]} perfiles borrados'))
                except ImportError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo importar modelos de users: {e}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error al borrar perfiles: {e}'))

                # ==================== RESUMEN ====================
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('✅ LIMPIEZA COMPLETADA'))
                self.stdout.write('='*60)
                self.stdout.write('\n📊 Resumen de registros borrados:\n')
                
                total = 0
                for model_name, count in sorted(counts.items()):
                    if count > 0:
                        self.stdout.write(f'   {model_name}: {count:,} registros')
                        total += count
                
                self.stdout.write(f'\n   Total: {total:,} registros borrados')
                
                # Mostrar usuarios permanentes mantenidos
                usuarios_permanentes = User.objects.filter(is_permanent=True)
                if usuarios_permanentes.exists():
                    self.stdout.write(f'\n👤 Usuarios permanentes mantenidos:')
                    for user in usuarios_permanentes:
                        self.stdout.write(f'   - {user.username} ({user.email}) - {user.rol}')
                
                self.stdout.write('\n' + '='*60 + '\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error durante la limpieza: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(f'Traceback completo:\n{traceback.format_exc()}'))
            raise

