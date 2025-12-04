from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.vehicles.models import Vehiculo, IngresoVehiculo
from apps.users.models import Profile
from apps.workorders.models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
    Aprobacion, Pausa, Checklist
)
from apps.drivers.models import Chofer, HistorialAsignacionVehiculo
from apps.scheduling.models import Agenda
from apps.emergencies.models import EmergenciaRuta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = "Crea datos de seed relacionados con vehículos existentes en el sistema"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar creación incluso si ya existen datos',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Verificar si ya hay datos (a menos que se use --force)
        if not options['force']:
            if User.objects.exclude(is_permanent=True).exists():
                self.stdout.write(self.style.WARNING(
                    '\n⚠️  Ya existen usuarios en el sistema.\n'
                    '   Use --force para crear datos de seed de todos modos.\n'
                ))
                return
        
        self.stdout.write('\n🌱 Creando datos de seed...\n')
        
        # ==================== CREAR USUARIOS (UNO POR ROL) ====================
        self.stdout.write('👤 Creando usuarios (uno por rol)...')
        usuarios_creados = {}
        
        roles_data = [
            ("ejecutivo", "ejecutivo@pgf.com", "EJECUTIVO", "ejecutivo123", "Ejecutivo", "PepsiCo"),
            ("supervisor", "supervisor@pgf.com", "SUPERVISOR", "supervisor123", "Supervisor", "Zona Norte"),
            ("jefe_taller", "jefe@pgf.com", "JEFE_TALLER", "jefe123", "Jefe", "Taller"),
            ("mecanico", "mecanico@pgf.com", "MECANICO", "mecanico123", "Juan", "Pérez"),
            ("guardia", "guardia@pgf.com", "GUARDIA", "guardia123", "Guardia", "Seguridad"),
            ("sponsor", "sponsor@pgf.com", "SPONSOR", "sponsor123", "Sponsor", "PepsiCo"),
            ("coordinador", "coordinador@pgf.com", "COORDINADOR_ZONA", "coord123", "Coordinador", "Zona"),
            ("recepcionista", "recepcionista@pgf.com", "RECEPCIONISTA", "recep123", "Recepcionista", "Taller"),
            ("chofer", "chofer@pgf.com", "CHOFER", "chofer123", "Chofer", "Flota"),
        ]
        
        for username, email, rol, password, first_name, last_name in roles_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "rol": rol,
                    "is_staff": rol in ["ADMIN", "SUPERVISOR", "EJECUTIVO"],
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            if created or options['force']:
                user.set_password(password)
                user.save()
                usuarios_creados[rol] = user
                
                # Crear perfil
                Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "notificaciones_email": True,
                        "notificaciones_sonido": True,
                    }
                )
                self.stdout.write(f'   ✅ Usuario {username} ({rol}) creado')
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(usuarios_creados)} usuarios creados\n'))
        
        # ==================== OBTENER VEHÍCULOS EXISTENTES ====================
        vehiculos = list(Vehiculo.objects.all()[:10])  # Tomar máximo 10 vehículos
        
        if not vehiculos:
            self.stdout.write(self.style.ERROR('❌ No hay vehículos en el sistema. Crea vehículos primero.'))
            return
        
        self.stdout.write(f'🚗 Usando {len(vehiculos)} vehículos existentes\n')
        
        # ==================== CREAR CHOFERES Y ASIGNAR A VEHÍCULOS ====================
        self.stdout.write('👨‍✈️ Creando choferes y asignaciones...')
        choferes_creados = []
        
        for i, vehiculo in enumerate(vehiculos[:5]):  # Máximo 5 choferes
            chofer, created = Chofer.objects.get_or_create(
                rut=f"1234567{i}",
                defaults={
                    "nombre_completo": f"Chofer {i+1}",
                    "telefono": f"+5691234567{i}",
                    "email": f"chofer{i+1}@pgf.com",
                    "zona": vehiculo.zona or "Norte",
                    "vehiculo_asignado": vehiculo,
                    "activo": True,
                }
            )
            if created or options['force']:
                choferes_creados.append(chofer)
                
                # Crear historial de asignación
                HistorialAsignacionVehiculo.objects.get_or_create(
                    chofer=chofer,
                    vehiculo=vehiculo,
                    activa=True,
                    defaults={
                        "fecha_asignacion": timezone.now() - timedelta(days=random.randint(1, 30)),
                    }
                )
                self.stdout.write(f'   ✅ Chofer {chofer.nombre_completo} asignado a {vehiculo.patente}')
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(choferes_creados)} choferes creados\n'))
        
        # ==================== CREAR INGRESOS DE VEHÍCULOS ====================
        self.stdout.write('🚪 Creando ingresos de vehículos...')
        ingresos_creados = []
        guardia = usuarios_creados.get("GUARDIA")
        
        if guardia:
            for vehiculo in vehiculos[:5]:  # Máximo 5 ingresos
                # Verificar si ya existe un ingreso para hoy
                ingreso_existente = IngresoVehiculo.objects.filter(
                    vehiculo=vehiculo,
                    fecha_ingreso__date=timezone.now().date()
                ).first()
                
                if ingreso_existente and not options['force']:
                    self.stdout.write(f'   ⚠️  Ingreso ya existe para {vehiculo.patente} hoy, omitiendo...')
                    continue
                
                # Crear nuevo ingreso
                ingreso = IngresoVehiculo.objects.create(
                    vehiculo=vehiculo,
                    guardia=guardia,
                    kilometraje=random.randint(50000, 200000),
                    observaciones=f"Ingreso para mantenimiento preventivo",
                )
                ingresos_creados.append(ingreso)
                self.stdout.write(f'   ✅ Ingreso creado para {vehiculo.patente}')
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(ingresos_creados)} ingresos creados\n'))
        
        # ==================== CREAR ÓRDENES DE TRABAJO ====================
        self.stdout.write('🔧 Creando órdenes de trabajo...')
        ots_creadas = []
        mecanico = usuarios_creados.get("MECANICO")
        supervisor = usuarios_creados.get("SUPERVISOR")
        jefe_taller = usuarios_creados.get("JEFE_TALLER")
        
        estados_ot = ["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA", "EN_QA", "CERRADA"]
        
        for i, vehiculo in enumerate(vehiculos[:6]):  # Máximo 6 OTs
            estado = estados_ot[i % len(estados_ot)]
            fecha_apertura = timezone.now() - timedelta(days=random.randint(0, 7))
            
            # Verificar si ya existe una OT para este vehículo en este estado
            ot_existente = OrdenTrabajo.objects.filter(
                vehiculo=vehiculo,
                estado=estado
            ).first()
            
            if ot_existente and not options['force']:
                self.stdout.write(f'   ⚠️  OT ya existe para {vehiculo.patente} en estado {estado}, omitiendo...')
                continue
            
            # Crear nueva OT
            ot = OrdenTrabajo.objects.create(
                vehiculo=vehiculo,
                estado=estado,
                responsable=mecanico if estado in ["EN_EJECUCION", "EN_PAUSA"] else None,
                supervisor=supervisor,
                jefe_taller=jefe_taller if estado == "EN_DIAGNOSTICO" else None,
                mecanico=mecanico if estado in ["EN_EJECUCION", "EN_PAUSA"] else None,
                motivo=f"Mantenimiento preventivo - {vehiculo.patente}",
                apertura=fecha_apertura,
                zona=vehiculo.zona or "Norte",
                prioridad=random.choice(["BAJA", "MEDIA", "ALTA"]),
            )
            
            if ot:
                ots_creadas.append(ot)
                
                # Agregar items a algunas OTs
                if estado in ["ABIERTA", "EN_EJECUCION"]:
                    ItemOT.objects.get_or_create(
                        ot=ot,
                        descripcion="Diagnóstico general",
                        defaults={
                            "tipo": "SERVICIO",
                            "cantidad": 1,
                            "costo_unitario": Decimal("50.00")
                        }
                    )
                
                # Si está cerrada, agregar fecha de cierre
                if estado == "CERRADA":
                    ot.cierre = fecha_apertura + timedelta(days=2)
                    ot.diagnostico = "Trabajo completado exitosamente"
                    ot.save()
                    
                    # Crear checklist
                    Checklist.objects.get_or_create(
                        ot=ot,
                        defaults={
                            "resultado": "OK",
                            "observaciones": "Todo conforme."
                        }
                    )
                
                # Agregar pausa a OT en pausa
                if estado == "EN_PAUSA" and mecanico:
                    Pausa.objects.get_or_create(
                        ot=ot,
                        usuario=mecanico,
                        fin__isnull=True,
                        defaults={
                            "motivo": "Esperando repuestos",
                            "inicio": timezone.now() - timedelta(hours=2)
                        }
                    )
                
                self.stdout.write(f'   ✅ OT {ot.id} creada para {vehiculo.patente} (estado: {estado})')
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(ots_creadas)} órdenes de trabajo creadas\n'))
        
        # ==================== CREAR AGENDAS ====================
        self.stdout.write('📅 Creando agendas...')
        agendas_creadas = []
        coordinador = usuarios_creados.get("COORDINADOR_ZONA")
        
        if coordinador:
            for vehiculo in vehiculos[:4]:  # Máximo 4 agendas
                fecha_agenda = timezone.now() + timedelta(days=random.randint(1, 30))
                
                # Verificar si ya existe una agenda para este vehículo en esta fecha
                agenda_existente = Agenda.objects.filter(
                    vehiculo=vehiculo,
                    fecha_programada__date=fecha_agenda.date()
                ).first()
                
                if agenda_existente and not options['force']:
                    self.stdout.write(f'   ⚠️  Agenda ya existe para {vehiculo.patente} el {fecha_agenda.date()}, omitiendo...')
                    continue
                
                # Crear nueva agenda
                agenda = Agenda.objects.create(
                    vehiculo=vehiculo,
                    coordinador=coordinador,
                    fecha_programada=fecha_agenda,
                    tipo_mantenimiento=random.choice(["PREVENTIVO", "CORRECTIVO", "EMERGENCIA"]),
                    motivo=f"Agenda programada para {vehiculo.patente}",
                    zona=vehiculo.zona or "Norte",
                )
                agendas_creadas.append(agenda)
                self.stdout.write(f'   ✅ Agenda creada para {vehiculo.patente} el {fecha_agenda.date()}')
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(agendas_creadas)} agendas creadas\n'))
        
        # ==================== CREAR EMERGENCIAS (Deshabilitado) ====================
        # App de emergencias deshabilitada
        self.stdout.write(self.style.WARNING('  ⚠️  Emergencias deshabilitadas (app removida)'))
        emergencias_creadas = []
        # if supervisor:
        #     for vehiculo in vehiculos[:3]:  # Máximo 3 emergencias
        #         emergencia, created = EmergenciaRuta.objects.get_or_create(
        #             vehiculo=vehiculo,
        #             estado="PENDIENTE",
        #             defaults={
        #                 "solicitante": supervisor,
        #                 "descripcion": f"Emergencia en ruta - {vehiculo.patente}",
        #                 "ubicacion": f"Ruta {random.randint(1, 100)} km {random.randint(1, 50)}",
        #                 "prioridad": random.choice(["MEDIA", "ALTA", "CRITICA"]),
        #             }
        #         )
        #         if created or options['force']:
        #             emergencias_creadas.append(emergencia)
        #             self.stdout.write(f'   ✅ Emergencia creada para {vehiculo.patente}')
        
        # self.stdout.write(self.style.SUCCESS(f'   ✅ {len(emergencias_creadas)} emergencias creadas\n'))
        
        # ==================== RESUMEN ====================
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ SEED COMPLETADO'))
        self.stdout.write('='*60)
        self.stdout.write('\n📊 Resumen de datos creados:\n')
        self.stdout.write(f'   👤 Usuarios: {len(usuarios_creados)}')
        self.stdout.write(f'   👨‍✈️ Choferes: {len(choferes_creados)}')
        self.stdout.write(f'   🚪 Ingresos: {len(ingresos_creados)}')
        self.stdout.write(f'   🔧 Órdenes de Trabajo: {len(ots_creadas)}')
        self.stdout.write(f'   📅 Agendas: {len(agendas_creadas)}')
        self.stdout.write(f'   🚨 Emergencias: {len(emergencias_creadas)}')
        
        self.stdout.write('\n🔑 Credenciales de acceso:\n')
        for username, _, rol, password, _, _ in roles_data:
            self.stdout.write(f'   👤 {username} / {password} ({rol})')
        
        self.stdout.write('\n' + '='*60 + '\n')

