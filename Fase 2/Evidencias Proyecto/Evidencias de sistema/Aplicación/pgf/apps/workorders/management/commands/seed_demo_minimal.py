"""
Comando para crear datos de demostración mínimos pero completos.

Crea:
- 1 usuario por cada rol (10 roles)
- 3 Órdenes de Trabajo con todas las relaciones
- 4-5 datos por sección (vehículos, choferes, repuestos, etc.)
- Todas las relaciones entre datos

Uso:
    python manage.py seed_demo_minimal
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import random
import uuid
from decimal import Decimal

from apps.users.models import Profile
from apps.vehicles.models import Vehiculo, Marca, IngresoVehiculo, EvidenciaIngreso
from apps.drivers.models import Chofer, HistorialAsignacionVehiculo
from apps.workorders.models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup, Aprobacion,
    Pausa, Checklist, Evidencia, ComentarioOT
)
# from apps.emergencies.models import EmergenciaRuta  # App eliminada
from apps.scheduling.models import Agenda, CupoDiario
from apps.inventory.models import (
    Repuesto, Stock, MovimientoStock, SolicitudRepuesto, HistorialRepuestoVehiculo
)


class Command(BaseCommand):
    help = "Crea datos de demostración mínimos pero completos con todas las relaciones"

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write(self.style.SUCCESS('\n🌱 Creando datos de demostración...\n'))
        
        with transaction.atomic():
            # ==================== 1. CREAR USUARIOS (UNO POR ROL) ====================
            self.stdout.write('👤 Creando usuarios (uno por rol)...')
            usuarios_por_rol = {}
            
            roles_data = [
                ("admin", "admin@pgf.com", "ADMIN", "admin123", "Administrador", "Sistema", True, True),
                ("ejecutivo", "ejecutivo@pgf.com", "EJECUTIVO", "ejecutivo123", "Ejecutivo", "PepsiCo", False, False),
                ("supervisor", "supervisor@pgf.com", "SUPERVISOR", "supervisor123", "Supervisor", "Zona Norte", True, False),
                ("jefe_taller", "jefe@pgf.com", "JEFE_TALLER", "jefe123", "Jefe", "Taller", False, False),
                ("mecanico", "mecanico@pgf.com", "MECANICO", "mecanico123", "Juan", "Pérez", False, False),
                ("guardia", "guardia@pgf.com", "GUARDIA", "guardia123", "Guardia", "Seguridad", False, False),
                ("sponsor", "sponsor@pgf.com", "SPONSOR", "sponsor123", "Sponsor", "PepsiCo", False, False),
                ("coordinador", "coordinador@pgf.com", "COORDINADOR_ZONA", "coord123", "Coordinador", "Zona", False, False),
                ("recepcionista", "recepcionista@pgf.com", "RECEPCIONISTA", "recep123", "Recepcionista", "Taller", False, False),
                ("chofer", "chofer@pgf.com", "CHOFER", "chofer123", "Chofer", "Flota", False, False),
            ]
            
            for username, email, rol, password, first_name, last_name, is_staff, is_superuser in roles_data:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "rol": rol,
                        "is_staff": is_staff,
                        "is_superuser": is_superuser,
                        "first_name": first_name,
                        "last_name": last_name,
                        "rut": f"1234567{roles_data.index((username, email, rol, password, first_name, last_name, is_staff, is_superuser))}-{random.randint(0, 9)}",
                    }
                )
                if created:
                    user.set_password(password)
                    user.save()
                    
                    # Crear perfil
                    Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            "phone_number": f"+5691234567{roles_data.index((username, email, rol, password, first_name, last_name, is_staff, is_superuser))}",
                            "notificaciones_email": True,
                            "notificaciones_push": True,
                            "notificaciones_sonido": True,
                        }
                    )
                
                usuarios_por_rol[rol] = user
                self.stdout.write(f'   ✅ {username} ({rol})')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(usuarios_por_rol)} usuarios creados\n'))
            
            # ==================== 2. OBTENER/CREAR MARCAS ====================
            self.stdout.write('🚗 Obteniendo marcas...')
            marcas = Marca.objects.filter(activa=True)[:5]
            if marcas.count() < 3:
                # Crear marcas si no hay suficientes
                marcas_nombres = ["Toyota", "Ford", "Chevrolet", "Nissan", "Hyundai"]
                for nombre in marcas_nombres:
                    marca, _ = Marca.objects.get_or_create(nombre=nombre, defaults={"activa": True})
                    if marca not in marcas:
                        marcas = list(marcas) + [marca]
            marcas = list(marcas)[:5]
            self.stdout.write(f'   ✅ {len(marcas)} marcas disponibles\n')
            
            # ==================== 3. CREAR VEHÍCULOS (5) ====================
            self.stdout.write('🚗 Creando vehículos...')
            vehiculos = []
            modelos_por_marca = {
                "Toyota": ["Hilux", "Corolla", "RAV4"],
                "Ford": ["Ranger", "Transit", "F-150"],
                "Chevrolet": ["Silverado", "Trailblazer", "Spark"],
                "Nissan": ["Navara", "Frontier", "Sentra"],
                "Hyundai": ["Tucson", "Santa Fe", "i20"],
            }
            
            patentes = ["AA1234", "BB5678", "CC9012", "DD3456", "EE7890"]
            zonas = ["Zona Norte", "Zona Centro", "Zona Sur"]
            
            supervisor = usuarios_por_rol.get("SUPERVISOR")
            
            for i, patente in enumerate(patentes):
                marca = marcas[i % len(marcas)]
                modelos_disponibles = modelos_por_marca.get(marca.nombre, ["Modelo Genérico"])
                modelo = modelos_disponibles[i % len(modelos_disponibles)]
                
                vehiculo, created = Vehiculo.objects.get_or_create(
                    patente=patente,
                    defaults={
                        "marca": marca,
                        "modelo": modelo,
                        "anio": 2020 + (i % 4),
                        "tipo": random.choice(["DIESEL", "ELECTRICO", "UTILITARIO"]),
                        "categoria": random.choice(["REPARTO", "VENTAS", "RESPALDO"]),
                        "estado": random.choice(["ACTIVO", "EN_ESPERA", "EN_MANTENIMIENTO"]),
                        "estado_operativo": random.choice(["OPERATIVO", "EN_TALLER", "BLOQUEADO"]),
                        "zona": zonas[i % len(zonas)],
                        "supervisor": supervisor,
                        "km_mensual_promedio": random.randint(1000, 5000),
                        "vin": f"VIN{random.randint(10000000000000000, 99999999999999999)}"[:17],
                    }
                )
                vehiculos.append(vehiculo)
                self.stdout.write(f'   ✅ {patente} - {marca.nombre} {modelo}')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(vehiculos)} vehículos creados\n'))
            
            # ==================== 4. CREAR CHOFERES (5) ====================
            self.stdout.write('👨‍✈️ Creando choferes...')
            choferes = []
            for i in range(5):
                chofer, created = Chofer.objects.get_or_create(
                    rut=f"1234567{i}-{random.randint(0, 9)}",
                    defaults={
                        "nombre_completo": f"Chofer {i+1}",
                        "telefono": f"+5691234567{i}",
                        "email": f"chofer{i+1}@pgf.com",
                        "zona": zonas[i % len(zonas)],
                        "vehiculo_asignado": vehiculos[i] if i < len(vehiculos) else None,
                        "activo": True,
                        "km_mensual_promedio": random.randint(1500, 6000),
                    }
                )
                choferes.append(chofer)
                
                # Crear historial de asignación
                if chofer.vehiculo_asignado:
                    HistorialAsignacionVehiculo.objects.get_or_create(
                        chofer=chofer,
                        vehiculo=chofer.vehiculo_asignado,
                        activa=True,
                        defaults={
                            "fecha_asignacion": timezone.now() - timedelta(days=random.randint(1, 30)),
                        }
                    )
                self.stdout.write(f'   ✅ {chofer.nombre_completo}')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(choferes)} choferes creados\n'))
            
            # ==================== 5. CREAR REPUESTOS (5) ====================
            self.stdout.write('🔧 Creando repuestos...')
            repuestos = []
            categorias = ["Frenos", "Motor", "Transmisión", "Suspensión", "Eléctrico"]
            marcas_repuestos = ["Bosch", "Delphi", "Valeo", "Continental", "TRW"]
            
            for i in range(5):
                codigo = f"REP-{categorias[i][:3].upper()}-{random.randint(1000, 9999)}"
                repuesto, created = Repuesto.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        "nombre": f"{categorias[i]} {marcas_repuestos[i]}",
                        "descripcion": f"Repuesto de {categorias[i]} marca {marcas_repuestos[i]}",
                        "marca": marcas_repuestos[i],
                        "categoria": categorias[i],
                        "precio_referencia": random.randint(5000, 500000),
                        "unidad_medida": "UNIDAD",
                        "activo": True,
                    }
                )
                
                # Crear stock
                Stock.objects.get_or_create(
                    repuesto=repuesto,
                    defaults={
                        "cantidad_actual": random.randint(10, 50),
                        "cantidad_minima": 5,
                        "ubicacion": f"Estante {i+1}-A",
                    }
                )
                
                repuestos.append(repuesto)
                self.stdout.write(f'   ✅ {repuesto.nombre}')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(repuestos)} repuestos creados\n'))
            
            # ==================== 6. CREAR INGRESOS DE VEHÍCULOS (5) ====================
            self.stdout.write('🚪 Creando ingresos de vehículos...')
            guardia = usuarios_por_rol.get("GUARDIA")
            ingresos = []
            
            for i, vehiculo in enumerate(vehiculos):
                ingreso, created = IngresoVehiculo.objects.get_or_create(
                    vehiculo=vehiculo,
                    fecha_ingreso__date=timezone.now().date() - timedelta(days=i),
                    defaults={
                        "guardia": guardia,
                        "kilometraje": random.randint(50000, 200000),
                        "observaciones": f"Ingreso para mantenimiento - {vehiculo.patente}",
                        "fecha_ingreso": timezone.now() - timedelta(days=i),
                    }
                )
                
                # Crear evidencias de ingreso
                for j in range(2):
                    EvidenciaIngreso.objects.get_or_create(
                        ingreso=ingreso,
                        tipo=random.choice(["FOTO_INGRESO", "FOTO_DANOS", "FOTO_DOCUMENTOS"]),
                        defaults={
                            "url": f"https://s3.amazonaws.com/bucket/evidencias/ingreso_{ingreso.id}_{uuid.uuid4()}.jpg",
                            "descripcion": f"Evidencia {j+1} del ingreso",
                        }
                    )
                
                ingresos.append(ingreso)
                self.stdout.write(f'   ✅ Ingreso para {vehiculo.patente}')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(ingresos)} ingresos creados\n'))
            
            # ==================== 7. CREAR 3 ÓRDENES DE TRABAJO CON TODAS LAS RELACIONES ====================
            self.stdout.write('🔨 Creando 3 órdenes de trabajo con todas las relaciones...')
            ots = []
            estados_ot = ["ABIERTA", "EN_EJECUCION", "CERRADA"]
            supervisor = usuarios_por_rol.get("SUPERVISOR")
            jefe_taller = usuarios_por_rol.get("JEFE_TALLER")
            mecanico = usuarios_por_rol.get("MECANICO")
            sponsor = usuarios_por_rol.get("SPONSOR")
            
            for i in range(3):
                vehiculo = vehiculos[i]
                estado = estados_ot[i]
                chofer = choferes[i] if i < len(choferes) else None
                
                # Crear OT
                ot, created = OrdenTrabajo.objects.get_or_create(
                    vehiculo=vehiculo,
                    estado=estado,
                    defaults={
                        "supervisor": supervisor,
                        "jefe_taller": jefe_taller if estado in ["EN_EJECUCION", "CERRADA"] else None,
                        "mecanico": mecanico if estado in ["EN_EJECUCION", "CERRADA"] else None,
                        "responsable": mecanico if estado in ["EN_EJECUCION", "CERRADA"] else supervisor,
                        "chofer": chofer,
                        "motivo": f"Mantenimiento preventivo - {vehiculo.patente}",
                        "diagnostico": f"Diagnóstico realizado: {vehiculo.marca.nombre} {vehiculo.modelo} requiere mantenimiento" if estado != "ABIERTA" else "",
                        "tipo": random.choice(["MANTENCION", "REPARACION", "DIAGNOSTICO"]),
                        "prioridad": random.choice(["BAJA", "MEDIA", "ALTA"]),
                        "zona": vehiculo.zona,
                        "apertura": timezone.now() - timedelta(days=7-i),
                        "fecha_diagnostico": timezone.now() - timedelta(days=6-i) if estado != "ABIERTA" else None,
                        "fecha_asignacion_mecanico": timezone.now() - timedelta(days=5-i) if estado in ["EN_EJECUCION", "CERRADA"] else None,
                        "fecha_inicio_ejecucion": timezone.now() - timedelta(days=4-i) if estado in ["EN_EJECUCION", "CERRADA"] else None,
                        "cierre": timezone.now() - timedelta(days=1-i) if estado == "CERRADA" else None,
                        "tiempo_espera": random.uniform(0.5, 2.0) if estado != "ABIERTA" else None,
                        "tiempo_ejecucion": random.uniform(1.0, 5.0) if estado in ["EN_EJECUCION", "CERRADA"] else None,
                        "tiempo_total_reparacion": random.uniform(1.5, 6.0) if estado == "CERRADA" else None,
                    }
                )
                
                if created:
                    # Crear Items de OT (3-4 items por OT)
                    num_items = random.randint(3, 4)
                    for j in range(num_items):
                        tipo_item = random.choice(["REPUESTO", "SERVICIO"])
                        repuesto = random.choice(repuestos) if tipo_item == "REPUESTO" else None
                        
                        ItemOT.objects.create(
                            ot=ot,
                            tipo=tipo_item,
                            descripcion=f"{repuesto.nombre if repuesto else 'Servicio de'} {random.choice(['Mantenimiento', 'Reparación', 'Revisión'])}" if tipo_item == "REPUESTO" else f"Servicio de {random.choice(['Diagnóstico', 'Alineación', 'Balanceo'])}",
                            cantidad=random.randint(1, 3),
                            costo_unitario=Decimal(random.randint(10000, 200000)),
                        )
                    
                    # Crear Presupuesto
                    total_items = sum(float(item.cantidad * item.costo_unitario) for item in ot.items.all())
                    umbral = 500000
                    requiere_aprob = total_items > umbral
                    
                    presupuesto, _ = Presupuesto.objects.get_or_create(
                        ot=ot,
                        defaults={
                            "total": Decimal(total_items),
                            "requiere_aprobacion": requiere_aprob,
                            "umbral": Decimal(umbral),
                        }
                    )
                    
                    # Crear Detalles de Presupuesto
                    for item in ot.items.all():
                        DetallePresup.objects.get_or_create(
                            presupuesto=presupuesto,
                            concepto=item.descripcion[:255],
                            defaults={
                                "cantidad": item.cantidad,
                                "precio": item.costo_unitario,
                            }
                        )
                    
                    # Crear Aprobación si requiere
                    if requiere_aprob and sponsor:
                        Aprobacion.objects.get_or_create(
                            presupuesto=presupuesto,
                            defaults={
                                "sponsor": sponsor,
                                "estado": random.choice(["PENDIENTE", "APROBADO"]),
                                "comentario": "Presupuesto aprobado para proceder",
                                "fecha": timezone.now() - timedelta(days=3-i),
                            }
                        )
                    
                    # Crear Pausas (si está en ejecución)
                    if estado == "EN_EJECUCION":
                        Pausa.objects.create(
                            ot=ot,
                            usuario=mecanico,
                            tipo=random.choice(["ESPERA_REPUESTO", "COLACION", "APROBACION_PENDIENTE"]),
                            motivo="Pausa por espera de repuestos",
                            inicio=timezone.now() - timedelta(hours=2),
                            fin=None,  # Pausa activa
                        )
                    
                    # Crear Evidencias (4-5 por OT)
                    num_evidencias = random.randint(4, 5)
                    for j in range(num_evidencias):
                        Evidencia.objects.create(
                            ot=ot,
                            url=f"https://s3.amazonaws.com/bucket/evidencias/ot_{ot.id}_{uuid.uuid4()}.jpg",
                            tipo=random.choice(["FOTO_ANTES", "FOTO_DURANTE", "FOTO_DESPUES", "DOCUMENTO"]),
                            descripcion=f"Evidencia {j+1} de la OT",
                            subido_por=random.choice([mecanico, jefe_taller, guardia]),
                        )
                    
                    # Crear Checklist (si está cerrada)
                    if estado == "CERRADA":
                        Checklist.objects.create(
                            ot=ot,
                            verificador=jefe_taller,
                            resultado="OK",
                            observaciones="Trabajo completado exitosamente. Todo conforme.",
                        )
                    
                    # Crear Comentarios (3-4 por OT)
                    num_comentarios = random.randint(3, 4)
                    usuarios_comentarios = [mecanico, jefe_taller, supervisor]
                    for j in range(num_comentarios):
                        usuario_comentario = random.choice(usuarios_comentarios)
                        ComentarioOT.objects.create(
                            ot=ot,
                            usuario=usuario_comentario,
                            contenido=f"Comentario {j+1}: Progreso del trabajo según lo planificado.",
                        )
                    
                    # Crear Solicitudes de Repuestos
                    for item in ot.items.filter(tipo="REPUESTO")[:2]:
                        repuesto_item = random.choice(repuestos)
                        SolicitudRepuesto.objects.create(
                            ot=ot,
                            item_ot=item,
                            repuesto=repuesto_item,
                            cantidad_solicitada=item.cantidad,
                            cantidad_entregada=item.cantidad if estado != "ABIERTA" else 0,
                            estado="ENTREGADA" if estado != "ABIERTA" else "PENDIENTE",
                            motivo=f"Solicitud de {repuesto_item.nombre} para OT",
                            solicitante=mecanico,
                            aprobador=jefe_taller if estado != "ABIERTA" else None,
                            entregador=usuarios_por_rol.get("ADMIN") if estado != "ABIERTA" else None,
                            fecha_solicitud=ot.apertura,
                            fecha_aprobacion=ot.apertura + timedelta(hours=1) if estado != "ABIERTA" else None,
                            fecha_entrega=ot.apertura + timedelta(hours=2) if estado != "ABIERTA" else None,
                        )
                
                ots.append(ot)
                self.stdout.write(f'   ✅ OT {ot.id} - {vehiculo.patente} ({estado})')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(ots)} órdenes de trabajo creadas\n'))
            
            # ==================== 8. CREAR EMERGENCIAS (Deshabilitado) ====================
            # App de emergencias deshabilitada
            self.stdout.write(self.style.WARNING('  ⚠️  Emergencias deshabilitadas (app removida)'))
            emergencias = []
            # coordinador = usuarios_por_rol.get("COORDINADOR_ZONA")
            # 
            # for i in range(4):
            #     vehiculo = vehiculos[i % len(vehiculos)]
            #     emergencia, created = EmergenciaRuta.objects.get_or_create(
            #         vehiculo=vehiculo,
            #         estado="SOLICITADA",
            #         defaults={
            #             "solicitante": coordinador,
            #             "aprobador": jefe_taller if i % 2 == 0 else None,
            #             "supervisor_asignado": supervisor if i % 2 == 0 else None,
            #             "mecanico_asignado": mecanico if i % 2 == 0 else None,
            #             "descripcion": f"Emergencia en ruta - {vehiculo.patente}",
            #             "ubicacion": f"Ruta {random.randint(1, 100)} km {random.randint(1, 50)}",
            #             "zona": vehiculo.zona,
            #             "prioridad": random.choice(["MEDIA", "ALTA", "CRITICA"]),
            #             "estado": random.choice(["SOLICITADA", "APROBADA", "ASIGNADA", "RESUELTA"]),
            #             "fecha_solicitud": timezone.now() - timedelta(days=random.randint(1, 7)),
            #         }
            #     )
            #     emergencias.append(emergencia)
            #     self.stdout.write(f'   ✅ Emergencia para {vehiculo.patente}')
            # 
            # self.stdout.write(self.style.SUCCESS(f'   ✅ {len(emergencias)} emergencias creadas\n'))
            
            # ==================== 9. CREAR AGENDAS (4) ====================
            self.stdout.write('📅 Creando agendas...')
            agendas = []
            
            for i in range(4):
                vehiculo = vehiculos[i % len(vehiculos)]
                agenda, created = Agenda.objects.get_or_create(
                    vehiculo=vehiculo,
                    fecha_programada__date=(timezone.now() + timedelta(days=i+1)).date(),
                    defaults={
                        "coordinador": coordinador,
                        "fecha_programada": timezone.now() + timedelta(days=i+1),
                        "tipo_mantenimiento": random.choice(["PREVENTIVO", "CORRECTIVO", "EMERGENCIA"]),
                        "motivo": f"Agenda programada para {vehiculo.patente}",
                        "zona": vehiculo.zona,
                        "estado": random.choice(["PROGRAMADA", "CONFIRMADA", "EN_PROCESO"]),
                        "ot_asociada": ots[i % len(ots)] if i < len(ots) else None,
                    }
                )
                agendas.append(agenda)
                self.stdout.write(f'   ✅ Agenda para {vehiculo.patente}')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(agendas)} agendas creadas\n'))
            
            # ==================== 10. CREAR MOVIMIENTOS DE STOCK (5) ====================
            self.stdout.write('📦 Creando movimientos de stock...')
            admin = usuarios_por_rol.get("ADMIN")
            
            for i, repuesto in enumerate(repuestos[:5]):
                stock = repuesto.stock
                MovimientoStock.objects.create(
                    repuesto=repuesto,
                    tipo=random.choice(["ENTRADA", "SALIDA", "AJUSTE"]),
                    cantidad=random.randint(1, 10),
                    cantidad_anterior=stock.cantidad_actual,
                    cantidad_nueva=stock.cantidad_actual + random.randint(-5, 10),
                    motivo=f"Movimiento de stock para {repuesto.nombre}",
                    usuario=admin,
                    ot=ots[i % len(ots)] if i < len(ots) else None,
                    vehiculo=vehiculos[i % len(vehiculos)] if i < len(vehiculos) else None,
                )
                self.stdout.write(f'   ✅ Movimiento para {repuesto.nombre}')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ 5 movimientos de stock creados\n'))
            
            # ==================== RESUMEN ====================
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✅ DATOS DE DEMOSTRACIÓN CREADOS EXITOSAMENTE'))
            self.stdout.write('='*60)
            self.stdout.write('\n📊 Resumen:\n')
            self.stdout.write(f'   👤 Usuarios: {len(usuarios_por_rol)} (uno por rol)')
            self.stdout.write(f'   🚗 Vehículos: {len(vehiculos)}')
            self.stdout.write(f'   👨‍✈️ Choferes: {len(choferes)}')
            self.stdout.write(f'   🔧 Repuestos: {len(repuestos)}')
            self.stdout.write(f'   🚪 Ingresos: {len(ingresos)}')
            self.stdout.write(f'   🔨 Órdenes de Trabajo: {len(ots)} (con todas las relaciones)')
            self.stdout.write(f'   🚨 Emergencias: {len(emergencias)}')
            self.stdout.write(f'   📅 Agendas: {len(agendas)}')
            self.stdout.write(f'   📦 Movimientos de stock: 5')
            
            self.stdout.write('\n🔑 Credenciales de acceso:\n')
            for username, _, rol, password, _, _, _, _ in roles_data:
                self.stdout.write(f'   👤 {username} / {password} ({rol})')
            
            self.stdout.write('\n' + '='*60 + '\n')

