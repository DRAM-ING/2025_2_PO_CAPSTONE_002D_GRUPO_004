"""
Comando de Django para generar datos de prueba completos para todos los módulos.

Este comando crea:
- Usuarios con todos los roles y campos completos
- Vehículos con todos los campos
- Choferes completos
- Órdenes de Trabajo en diferentes estados
- Items de OT, Presupuestos, Evidencias, Pausas, Checklists, Comentarios
- Emergencias
- Agenda y Cupos diarios
- Repuestos e Inventario
- Movimientos de stock
- Ingresos de vehículos
- Asignaciones de vehículos a choferes

Uso:
    python manage.py seed_completo
    python manage.py seed_completo --users 20 --vehicles 30 --workorders 50
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, datetime
import random
import uuid

from apps.users.models import Profile
from apps.vehicles.models import Vehiculo, IngresoVehiculo, EvidenciaIngreso
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

# Importar Faker
try:
    from faker import Faker
    fake = Faker('es_CL')  # Español de Chile
except ImportError:
    raise ImportError("Faker no está instalado. Ejecuta: poetry add --group dev faker")


def calcular_digito_verificador(rut_sin_dv):
    """Calcula el dígito verificador de un RUT chileno"""
    rut = str(rut_sin_dv).replace('.', '').replace('-', '')
    rut = rut[:-1] if len(rut) > 1 and rut[-1].isdigit() == False else rut
    
    if not rut.isdigit():
        return '0'
    
    rut = int(rut)
    suma = 0
    multiplicador = 2
    
    while rut > 0:
        suma += (rut % 10) * multiplicador
        rut //= 10
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    resto = suma % 11
    dv = 11 - resto
    
    if dv == 11:
        return '0'
    elif dv == 10:
        return 'K'
    else:
        return str(dv)


def generar_rut():
    """Genera un RUT chileno válido"""
    rut_sin_dv = random.randint(1000000, 25000000)
    dv = calcular_digito_verificador(rut_sin_dv)
    return f"{rut_sin_dv}{dv}"


def generar_patente():
    """Genera una patente chilena válida"""
    formatos = [
        lambda: f"{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.randint(1000, 9999)}",  # AA1234
        lambda: f"{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.randint(10, 99)}",  # AAAA12
        lambda: f"{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.randint(10, 99)}",  # AAAB12
    ]
    return random.choice(formatos)()


class Command(BaseCommand):
    help = "Genera datos de prueba completos para todos los módulos de la aplicación"

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=30,
            help='Número de usuarios a crear (default: 30)',
        )
        parser.add_argument(
            '--vehicles',
            type=int,
            default=50,
            help='Número de vehículos a crear (default: 50)',
        )
        parser.add_argument(
            '--workorders',
            type=int,
            default=80,
            help='Número de órdenes de trabajo a crear (default: 80)',
        )
        parser.add_argument(
            '--drivers',
            type=int,
            default=25,
            help='Número de choferes a crear (default: 25)',
        )
        parser.add_argument(
            '--emergencies',
            type=int,
            default=15,
            help='Número de emergencias a crear (default: 15) - DESHABILITADO',
        )
        parser.add_argument(
            '--agendas',
            type=int,
            default=20,
            help='Número de agendas a crear (default: 20)',
        )
        parser.add_argument(
            '--repuestos',
            type=int,
            default=100,
            help='Número de repuestos a crear (default: 100)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        num_users = options['users']
        num_vehicles = options['vehicles']
        num_workorders = options['workorders']
        num_drivers = options['drivers']
        num_emergencies = options['emergencies']
        num_agendas = options['agendas']
        num_repuestos = options['repuestos']

        self.stdout.write(self.style.SUCCESS('\n🌱 Iniciando generación de datos de prueba...\n'))

        with transaction.atomic():
            # 0. CREAR SUPERUSUARIO ADMIN (siempre se crea/actualiza)
            self.stdout.write('👤 Creando/verificando superusuario admin...')
            User = get_user_model()
            admin_username = 'admin'
            admin_email = 'admin@pepsico.cl'
            admin_rut = '12345678-9'  # RUT fijo para el admin
            
            admin_user, created = User.objects.get_or_create(
                username=admin_username,
                defaults={
                    'email': admin_email,
                    'rut': admin_rut,
                    'first_name': 'Administrador',
                    'last_name': 'Sistema',
                    'rol': 'ADMIN',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            # Si ya existe, asegurar que tenga los permisos correctos (no se puede borrar)
            if not created:
                admin_user.email = admin_email
                admin_user.rut = admin_rut
                admin_user.rol = 'ADMIN'
                admin_user.is_active = True
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.first_name = 'Administrador'
                admin_user.last_name = 'Sistema'
                admin_user.save()
            
            # Establecer contraseña (siempre actualizar para asegurar que sea 'admin123')
            admin_user.set_password('admin123')
            admin_user.save()
            
            # Asegurar que el perfil exista y esté completo
            if hasattr(admin_user, 'profile'):
                profile = admin_user.profile
                profile.phone_number = '+56912345678'
                profile.notificaciones_email = True
                profile.notificaciones_push = True
                profile.notificaciones_sonido = True
                profile.save()
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Superusuario "{admin_username}" creado (contraseña: admin123)\n'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Superusuario "{admin_username}" verificado/actualizado (contraseña: admin123)\n'))
            
            # 1. CREAR USUARIOS ADICIONALES
            self.stdout.write('👥 Creando usuarios adicionales...')
            usuarios_por_rol = {}
            roles = [
                'ADMIN', 'SUPERVISOR', 'JEFE_TALLER', 'MECANICO', 'GUARDIA',
                'COORDINADOR_ZONA', 'RECEPCIONISTA', 'EJECUTIVO', 'SPONSOR', 'CHOFER'
            ]
            
            for rol in roles:
                usuarios_por_rol[rol] = []
            
            # Agregar el admin a la lista (siempre estará disponible)
            usuarios_por_rol['ADMIN'].append(admin_user)
            
            zonas = ['Zona Norte', 'Zona Centro', 'Zona Sur', 'Zona Metropolitana']
            sucursales = ['Sucursal 1', 'Sucursal 2', 'Sucursal 3', 'Sucursal 4']
            
            for i in range(num_users):
                rol = random.choice(roles)
                
                # Generar username único
                username = f"{rol.lower()}{i+1}"
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{rol.lower()}{i+1}_{counter}"
                    counter += 1
                
                # Generar email único
                email = f"{username}@pepsico.cl"
                counter_email = 1
                while User.objects.filter(email=email).exists():
                    email = f"{username}{counter_email}@pepsico.cl"
                    counter_email += 1
                
                # Generar RUT único
                rut = generar_rut()
                while User.objects.filter(rut=rut).exists():
                    rut = generar_rut()
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',  # Contraseña por defecto
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    rol=rol,
                    rut=rut,
                    is_active=True,
                    is_staff=(rol == 'ADMIN'),
                    is_superuser=(rol == 'ADMIN'),
                )
                
                # Crear perfil completo
                profile = user.profile
                profile.phone_number = fake.phone_number()[:20]
                profile.notificaciones_email = random.choice([True, False])
                profile.notificaciones_push = random.choice([True, False])
                profile.notificaciones_sonido = random.choice([True, False])
                profile.save()
                
                usuarios_por_rol[rol].append(user)
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'  ✓ {i + 1}/{num_users} usuarios creados')
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {num_users} usuarios creados\n'))

            # 2. CREAR VEHÍCULOS
            self.stdout.write('🚗 Creando vehículos...')
            vehiculos = []
            marcas = ['Toyota', 'Ford', 'Chevrolet', 'Nissan', 'Hyundai', 'Kia', 'Volkswagen', 'Mercedes-Benz']
            modelos_por_marca = {
                'Toyota': ['Hilux', 'Corolla', 'RAV4', 'Yaris'],
                'Ford': ['Ranger', 'Transit', 'F-150', 'Escape'],
                'Chevrolet': ['Silverado', 'Trailblazer', 'Spark', 'Cruze'],
                'Nissan': ['Navara', 'Frontier', 'Sentra', 'Kicks'],
                'Hyundai': ['Tucson', 'Santa Fe', 'i20', 'i30'],
                'Kia': ['Sportage', 'Sorento', 'Rio', 'Picanto'],
                'Volkswagen': ['Amarok', 'Tiguan', 'Gol', 'Polo'],
                'Mercedes-Benz': ['Sprinter', 'Vito', 'Actros', 'Atego'],
            }
            tipos = ['ELECTRICO', 'DIESEL', 'UTILITARIO', 'REPARTO', 'VENTAS', 'RESPALDO']
            categorias = ['REPARTO', 'VENTAS', 'RESPALDO']
            estados = ['ACTIVO', 'EN_ESPERA', 'EN_MANTENIMIENTO', 'BAJA']
            estados_operativos = ['OPERATIVO', 'EN_TALLER', 'BLOQUEADO', 'FUERA_POLITICA']
            
            supervisores = usuarios_por_rol['SUPERVISOR'] + usuarios_por_rol['COORDINADOR_ZONA']
            
            for i in range(num_vehicles):
                marca = random.choice(marcas)
                modelo = random.choice(modelos_por_marca.get(marca, ['Modelo Genérico']))
                patente = generar_patente()
                
                # Asegurar que la patente sea única
                while Vehiculo.objects.filter(patente=patente).exists():
                    patente = generar_patente()
                
                vehiculo = Vehiculo.objects.create(
                    patente=patente,
                    marca=marca,
                    modelo=modelo,
                    anio=random.randint(2018, 2024),
                    tipo=random.choice(tipos),
                    categoria=random.choice(categorias),
                    estado=random.choice(estados),
                    estado_operativo=random.choice(estados_operativos),
                    vin=f"VIN{random.randint(10000000000000000, 99999999999999999)}"[:17],
                    zona=random.choice(zonas),
                    sucursal=random.choice(sucursales),
                    supervisor=random.choice(supervisores) if supervisores else None,
                    km_mensual_promedio=random.randint(1000, 5000),
                    ceco=fake.bothify(text='####-####')[:9],
                    cumplimiento=random.randint(80, 100),
                )
                vehiculos.append(vehiculo)
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'  ✓ {i + 1}/{num_vehicles} vehículos creados')
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {num_vehicles} vehículos creados\n'))

            # 3. CREAR CHOFERES
            self.stdout.write('🚛 Creando choferes...')
            choferes = []
            for i in range(num_drivers):
                rut = generar_rut()
                while Chofer.objects.filter(rut=rut).exists():
                    rut = generar_rut()
                
                chofer = Chofer.objects.create(
                    nombre_completo=fake.name(),
                    rut=rut,
                    telefono=fake.phone_number()[:20],
                    email=fake.email(),
                    zona=random.choice(zonas),
                    sucursal=random.choice(sucursales),
                    vehiculo_asignado=random.choice(vehiculos) if vehiculos else None,
                    km_mensual_promedio=random.randint(1500, 6000),
                    activo=random.choice([True, True, True, False]),  # 75% activos
                    fecha_ingreso=fake.date_between(start_date='-2y', end_date='today'),
                    observaciones=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                )
                choferes.append(chofer)
            
            # Crear historial de asignaciones
            for chofer in choferes[:num_drivers//2]:  # Solo para la mitad
                if chofer.vehiculo_asignado:
                    HistorialAsignacionVehiculo.objects.create(
                        chofer=chofer,
                        vehiculo=chofer.vehiculo_asignado,
                        fecha_asignacion=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()),
                        activa=True,
                    )
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {num_drivers} choferes creados\n'))

            # 4. CREAR REPUESTOS E INVENTARIO
            self.stdout.write('🔧 Creando repuestos e inventario...')
            repuestos = []
            categorias_repuestos = ['Frenos', 'Motor', 'Transmisión', 'Suspensión', 'Eléctrico', 'Carrocería', 'Neumáticos', 'Filtros']
            marcas_repuestos = ['Bosch', 'Delphi', 'Valeo', 'Continental', 'TRW', 'Monroe', 'Bridgestone', 'Michelin']
            
            for i in range(num_repuestos):
                categoria = random.choice(categorias_repuestos)
                marca = random.choice(marcas_repuestos)
                codigo = f"{categoria[:3].upper()}-{marca[:3].upper()}-{random.randint(1000, 9999)}"
                
                while Repuesto.objects.filter(codigo=codigo).exists():
                    codigo = f"{categoria[:3].upper()}-{marca[:3].upper()}-{random.randint(1000, 9999)}"
                
                repuesto = Repuesto.objects.create(
                    codigo=codigo,
                    nombre=f"{categoria} {marca} {fake.word().capitalize()}",
                    descripcion=fake.text(max_nb_chars=300),
                    marca=marca,
                    categoria=categoria,
                    precio_referencia=random.randint(5000, 500000),
                    unidad_medida=random.choice(['UNIDAD', 'LITRO', 'KILO', 'METRO']),
                    activo=random.choice([True, True, False]),  # 66% activos
                )
                
                # Crear stock
                cantidad_actual = random.randint(0, 100)
                Stock.objects.create(
                    repuesto=repuesto,
                    cantidad_actual=cantidad_actual,
                    cantidad_minima=random.randint(5, 20),
                    ubicacion=f"Estante {random.randint(1, 50)}-{random.choice(['A', 'B', 'C', 'D'])}",
                )
                
                repuestos.append(repuesto)
                if (i + 1) % 20 == 0:
                    self.stdout.write(f'  ✓ {i + 1}/{num_repuestos} repuestos creados')
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {num_repuestos} repuestos creados\n'))

            # 5. CREAR INGRESOS DE VEHÍCULOS
            self.stdout.write('📥 Creando ingresos de vehículos...')
            guardias = usuarios_por_rol['GUARDIA'] + usuarios_por_rol['ADMIN']
            ingresos = []
            
            for vehiculo in vehiculos[:num_vehicles//2]:  # Ingresos para la mitad de vehículos
                guardia_ingreso = random.choice(guardias) if guardias else None
                if not guardia_ingreso:
                    continue  # Saltar si no hay guardias
                
                fecha_ing = fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.get_current_timezone())
                tiene_salida = random.choice([True, False])
                
                ingreso = IngresoVehiculo.objects.create(
                    vehiculo=vehiculo,
                    guardia=guardia_ingreso,
                    kilometraje=random.randint(10000, 200000),
                    observaciones=fake.text(max_nb_chars=300),
                    fecha_salida=fake.date_time_between(start_date=fecha_ing, end_date='now', tzinfo=timezone.get_current_timezone()) if tiene_salida else None,
                    guardia_salida=random.choice(guardias) if guardias and tiene_salida else None,
                    kilometraje_salida=random.randint(10000, 200000) if tiene_salida else None,
                    observaciones_salida=fake.text(max_nb_chars=200) if tiene_salida else '',
                    salio=tiene_salida,
                    qr_code=f"QR{random.randint(100000, 999999)}" if random.choice([True, False]) else '',
                )
                
                # Actualizar fecha_ingreso manualmente ya que auto_now_add no permite override
                IngresoVehiculo.objects.filter(id=ingreso.id).update(fecha_ingreso=fecha_ing)
                ingresos.append(ingreso)
                
                # Crear evidencias de ingreso
                for _ in range(random.randint(1, 3)):
                    EvidenciaIngreso.objects.create(
                        ingreso=ingreso,
                        url=f"https://s3.amazonaws.com/bucket/evidencias/ingreso_{ingreso.id}_{uuid.uuid4()}.jpg",
                        tipo=random.choice(['FOTO_INGRESO', 'FOTO_DANOS', 'FOTO_DOCUMENTOS', 'OTRO']),
                        descripcion=fake.text(max_nb_chars=100),
                    )
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {len(ingresos)} ingresos creados\n'))

            # 6. CREAR ÓRDENES DE TRABAJO
            self.stdout.write('🔨 Creando órdenes de trabajo...')
            ots = []
            estados_ot = ['ABIERTA', 'EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_PAUSA', 'EN_QA', 'RETRABAJO', 'CERRADA', 'ANULADA']
            tipos_ot = ['MANTENCION', 'REPARACION', 'DIAGNOSTICO', 'OTRO']  # EMERGENCIA removido
            prioridades = ['CRITICA', 'ALTA', 'MEDIA', 'BAJA']
            
            supervisores_ot = usuarios_por_rol['SUPERVISOR'] + usuarios_por_rol['COORDINADOR_ZONA']
            jefes_taller = usuarios_por_rol['JEFE_TALLER']
            mecanicos = usuarios_por_rol['MECANICO']
            
            for i in range(num_workorders):
                vehiculo = random.choice(vehiculos)
                estado = random.choice(estados_ot)
                
                # Asegurar que no haya múltiples OTs activas para el mismo vehículo
                if estado in ['ABIERTA', 'EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_PAUSA', 'EN_QA']:
                    if OrdenTrabajo.objects.filter(vehiculo=vehiculo, estado__in=['ABIERTA', 'EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_PAUSA', 'EN_QA']).exists():
                        estado = random.choice(['CERRADA', 'ANULADA'])
                
                ot = OrdenTrabajo.objects.create(
                    vehiculo=vehiculo,
                    supervisor=random.choice(supervisores_ot) if supervisores_ot else None,
                    jefe_taller=random.choice(jefes_taller) if jefes_taller and estado in ['EN_DIAGNOSTICO', 'EN_QA', 'CERRADA'] else None,
                    mecanico=random.choice(mecanicos) if mecanicos and estado in ['EN_EJECUCION', 'EN_PAUSA', 'RETRABAJO'] else None,
                    responsable=random.choice(supervisores_ot + mecanicos) if (supervisores_ot or mecanicos) else None,
                    chofer=random.choice(choferes) if choferes and random.choice([True, False]) else None,
                    estado=estado,
                    tipo=random.choice(tipos_ot),
                    prioridad=random.choice(prioridades),
                    motivo=fake.text(max_nb_chars=500),
                    diagnostico=fake.text(max_nb_chars=500) if estado in ['EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_QA', 'CERRADA'] else '',
                    zona=vehiculo.zona,
                    cierre=fake.date_time_between(start_date='-5m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado == 'CERRADA' else None,
                    tiempo_espera=random.uniform(0.5, 5.0) if estado in ['EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_QA', 'CERRADA'] else None,
                    tiempo_ejecucion=random.uniform(1.0, 20.0) if estado in ['EN_EJECUCION', 'EN_QA', 'CERRADA'] else None,
                    tiempo_total_reparacion=random.uniform(1.0, 15.0) if estado == 'CERRADA' else None,
                    fecha_diagnostico=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_QA', 'CERRADA'] else None,
                    fecha_asignacion_mecanico=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['EN_EJECUCION', 'EN_PAUSA', 'EN_QA', 'RETRABAJO', 'CERRADA'] else None,
                    fecha_inicio_ejecucion=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['EN_EJECUCION', 'EN_PAUSA', 'EN_QA', 'RETRABAJO', 'CERRADA'] else None,
                )
                
                # Actualizar fecha de apertura manualmente
                fecha_apertura = fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone())
                OrdenTrabajo.objects.filter(id=ot.id).update(apertura=fecha_apertura)
                ots.append(ot)
                
                # Crear items de OT
                num_items = random.randint(1, 5)
                for j in range(num_items):
                    tipo_item = random.choice(['REPUESTO', 'SERVICIO'])
                    repuesto = random.choice(repuestos) if repuestos and tipo_item == 'REPUESTO' else None
                    descripcion = f"{repuesto.nombre if repuesto else 'Servicio de'} {fake.word().capitalize()}" if tipo_item == 'REPUESTO' else fake.text(max_nb_chars=200)
                    
                    ItemOT.objects.create(
                        ot=ot,
                        tipo=tipo_item,
                        descripcion=descripcion,
                        cantidad=random.randint(1, 5),
                        costo_unitario=random.randint(5000, 200000),
                    )
                
                # Crear presupuesto para algunas OTs
                if random.choice([True, False]) and estado in ['EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_QA', 'CERRADA']:
                    # Calcular total sumando los items
                    total_presupuesto = sum(float(item.cantidad * item.costo_unitario) for item in ot.items.all()[:3])
                    if total_presupuesto == 0:
                        total_presupuesto = random.randint(100000, 3000000)
                    
                    umbral_presupuesto = random.randint(500000, 2000000)
                    requiere_aprob = total_presupuesto > umbral_presupuesto
                    
                    presupuesto = Presupuesto.objects.create(
                        ot=ot,
                        total=total_presupuesto,
                        requiere_aprobacion=requiere_aprob,
                        umbral=umbral_presupuesto,
                    )
                    
                    # Crear detalles de presupuesto
                    for item in ot.items.all()[:3]:
                        DetallePresup.objects.create(
                            presupuesto=presupuesto,
                            concepto=item.descripcion[:255],  # Limitar a 255 caracteres
                            cantidad=item.cantidad,
                            precio=item.costo_unitario,
                        )
                    
                    # Crear aprobación si requiere aprobación
                    if requiere_aprob:
                        sponsors = usuarios_por_rol['SPONSOR'] + usuarios_por_rol['EJECUTIVO']
                        if sponsors:
                            estado_aprob = random.choice(['PENDIENTE', 'APROBADO', 'RECHAZADO'])
                            fecha_aprob = fake.date_time_between(start_date=presupuesto.ot.apertura, end_date='now', tzinfo=timezone.get_current_timezone())
                            aprobacion = Aprobacion.objects.create(
                                presupuesto=presupuesto,
                                sponsor=random.choice(sponsors),
                                estado=estado_aprob,
                                comentario=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                            )
                            # Actualizar fecha manualmente
                            Aprobacion.objects.filter(id=aprobacion.id).update(fecha=fecha_aprob)
                
                # Crear pausas para OTs en ejecución
                if estado in ['EN_EJECUCION', 'EN_PAUSA']:
                    num_pausas = random.randint(1, 3)
                    usuarios_pausa = mecanicos + jefes_taller + supervisores_ot
                    if usuarios_pausa:
                        for _ in range(num_pausas):
                            inicio = fake.date_time_between(start_date=ot.apertura, end_date='now', tzinfo=timezone.get_current_timezone())
                            tiene_fin = random.choice([True, False])
                            pausa = Pausa.objects.create(
                                ot=ot,
                                usuario=random.choice(usuarios_pausa),
                                tipo=random.choice(['ESPERA_REPUESTO', 'APROBACION_PENDIENTE', 'COLACION', 'OTRO', 'ADMINISTRATIVA']),
                                motivo=fake.text(max_nb_chars=255),
                                es_automatica=(random.choice([True, False]) and random.choice([True, False])),  # Algunas automáticas
                            )
                            # Actualizar fechas manualmente
                            Pausa.objects.filter(id=pausa.id).update(
                                inicio=inicio,
                                fin=inicio + timedelta(hours=random.randint(1, 3)) if tiene_fin else None,
                            )
                
                # Crear evidencias
                num_evidencias = random.randint(2, 8)
                for _ in range(num_evidencias):
                    Evidencia.objects.create(
                        ot=ot,
                        url=f"https://s3.amazonaws.com/bucket/evidencias/ot_{ot.id}_{uuid.uuid4()}.jpg",
                        tipo=random.choice(['FOTO_ANTES', 'FOTO_DURANTE', 'FOTO_DESPUES', 'DOCUMENTO', 'OTRO']),
                        descripcion=fake.text(max_nb_chars=200),
                        subido_por=random.choice(mecanicos + jefes_taller + guardias) if (mecanicos or jefes_taller or guardias) else None,
                    )
                
                # Crear checklists para OTs en QA o cerradas
                if estado in ['EN_QA', 'CERRADA']:
                    Checklist.objects.create(
                        ot=ot,
                        verificador=random.choice(jefes_taller) if jefes_taller else None,
                        resultado=random.choice(['OK', 'NO_OK']),
                        observaciones=fake.text(max_nb_chars=300) if random.choice([True, False]) else '',
                    )
                
                # Crear comentarios
                num_comentarios = random.randint(1, 5)
                usuarios_comentarios = mecanicos + jefes_taller + supervisores_ot
                for _ in range(num_comentarios):
                    usuario_comentario = random.choice(usuarios_comentarios) if usuarios_comentarios else None
                    menciones_list = []
                    if usuarios_comentarios and len(usuarios_comentarios) > 1:
                        # Crear menciones (usernames con @)
                        usuarios_para_mención = [u for u in usuarios_comentarios if u != usuario_comentario]
                        if usuarios_para_mención:
                            num_menciones = min(2, len(usuarios_para_mención))
                            menciones_list = [f"@{u.username}" for u in random.sample(usuarios_para_mención, k=num_menciones)]
                    
                    ComentarioOT.objects.create(
                        ot=ot,
                        usuario=usuario_comentario,
                        contenido=fake.text(max_nb_chars=500),
                        menciones=menciones_list,
                    )
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'  ✓ {i + 1}/{num_workorders} OTs creadas')
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {num_workorders} órdenes de trabajo creadas\n'))

            # 7. CREAR EMERGENCIAS (Deshabilitado)
            # App de emergencias deshabilitada
            self.stdout.write(self.style.WARNING(f'  ⚠️  Emergencias deshabilitadas (app removida)\n'))
            # coordinadores = usuarios_por_rol['COORDINADOR_ZONA'] + usuarios_por_rol['SUPERVISOR']
            # estados_emergencia = ['SOLICITADA', 'APROBADA', 'ASIGNADA', 'EN_CAMINO', 'EN_REPARACION', 'RESUELTA', 'CERRADA', 'RECHAZADA']
            # 
            # for i in range(num_emergencies):
            #     vehiculo = random.choice(vehiculos)
            #     estado = random.choice(estados_emergencia)
            #     solicitante = random.choice(coordinadores) if coordinadores else None
            #     
            #     # Si no hay coordinadores, saltar esta emergencia
            #     if not solicitante:
            #         continue
            #     
            #     emergencia = EmergenciaRuta.objects.create(
            #         vehiculo=vehiculo,
            #         solicitante=solicitante,
            #         aprobador=random.choice(jefes_taller) if jefes_taller and estado in ['APROBADA', 'ASIGNADA', 'EN_CAMINO', 'EN_REPARACION', 'RESUELTA', 'CERRADA'] else None,
            #         supervisor_asignado=random.choice(supervisores_ot) if supervisores_ot and estado in ['ASIGNADA', 'EN_CAMINO', 'EN_REPARACION', 'RESUELTA', 'CERRADA'] else None,
            #         mecanico_asignado=random.choice(mecanicos) if mecanicos and estado in ['EN_REPARACION', 'RESUELTA', 'CERRADA'] else None,
            #         descripcion=fake.text(max_nb_chars=500),
            #         ubicacion=f"{fake.city()}, {fake.street_address()}",
            #         zona=vehiculo.zona,
            #         prioridad=random.choice(['CRITICA', 'ALTA', 'MEDIA']),
            #         estado=estado,
            #         fecha_solicitud=fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.get_current_timezone()),
            #         fecha_aprobacion=fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['APROBADA', 'ASIGNADA', 'EN_CAMINO', 'EN_REPARACION', 'RESUELTA', 'CERRADA'] else None,
            #         fecha_asignacion=fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['ASIGNADA', 'EN_CAMINO', 'EN_REPARACION', 'RESUELTA', 'CERRADA'] else None,
            #         fecha_resolucion=fake.date_time_between(start_date='-2m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['RESUELTA', 'CERRADA'] else None,
            #         fecha_cierre=fake.date_time_between(start_date='-1m', end_date='now', tzinfo=timezone.get_current_timezone()) if estado == 'CERRADA' else None,
            #         observaciones=fake.text(max_nb_chars=300) if random.choice([True, False]) else '',
            #         ot_asociada=random.choice(ots) if ots and random.choice([True, False]) else None,
            #     )
            # 
            # self.stdout.write(self.style.SUCCESS(f'  ✅ {num_emergencies} emergencias creadas\n'))

            # 8. CREAR AGENDA Y CUPOS
            self.stdout.write('📅 Creando agenda y cupos...')
            coordinadores_agenda = usuarios_por_rol['COORDINADOR_ZONA']
            estados_agenda = ['PROGRAMADA', 'CONFIRMADA', 'EN_PROCESO', 'COMPLETADA', 'CANCELADA', 'REPROGRAMADA']
            
            # Crear cupos diarios para los próximos 30 días
            # Nota: El modelo tiene fecha como unique, así que solo creamos uno por fecha
            for i in range(30):
                fecha = timezone.now().date() + timedelta(days=i)
                # Verificar si ya existe un cupo para esta fecha
                cupo, created = CupoDiario.objects.get_or_create(
                    fecha=fecha,
                    defaults={
                        'cupos_totales': random.randint(5, 15),
                        'cupos_ocupados': random.randint(0, 10),
                        'zona': random.choice(zonas) if zonas else '',
                    }
                )
                if not created:
                    # Si ya existe, actualizar los cupos
                    cupo.cupos_totales = random.randint(5, 15)
                    cupo.cupos_ocupados = random.randint(0, 10)
                    cupo.save()
            
            for i in range(num_agendas):
                vehiculo = random.choice(vehiculos)
                estado = random.choice(estados_agenda)
                coordinador = random.choice(coordinadores_agenda) if coordinadores_agenda else None
                
                # Si no hay coordinadores, saltar esta agenda
                if not coordinador:
                    continue
                
                fecha_programada = fake.date_time_between(start_date='-1m', end_date='+2m', tzinfo=timezone.get_current_timezone())
                
                agenda = Agenda.objects.create(
                    vehiculo=vehiculo,
                    coordinador=coordinador,
                    fecha_programada=fecha_programada,
                    motivo=fake.text(max_nb_chars=300),
                    tipo_mantenimiento=random.choice(['PREVENTIVO', 'CORRECTIVO']),  # EMERGENCIA removido
                    zona=vehiculo.zona,
                    estado=estado,
                    observaciones=fake.text(max_nb_chars=300) if random.choice([True, False]) else '',
                    ot_asociada=random.choice(ots) if ots and estado in ['EN_PROCESO', 'COMPLETADA'] and random.choice([True, False]) else None,
                )
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ {num_agendas} agendas creadas\n'))

            # 9. CREAR MOVIMIENTOS DE STOCK
            self.stdout.write('📦 Creando movimientos de stock...')
            usuarios_stock = usuarios_por_rol['ADMIN'] + usuarios_por_rol['JEFE_TALLER']
            
            if usuarios_stock:
                for repuesto in repuestos[:num_repuestos//2]:
                    stock = repuesto.stock
                    cantidad_anterior = stock.cantidad_actual
                    
                    # Crear algunos movimientos
                    for _ in range(random.randint(1, 3)):
                        tipo = random.choice(['ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION'])
                        cantidad = random.randint(1, 20)
                        
                        if tipo == 'ENTRADA':
                            cantidad_nueva = cantidad_anterior + cantidad
                        elif tipo == 'SALIDA':
                            cantidad_nueva = max(0, cantidad_anterior - cantidad)
                        elif tipo == 'AJUSTE':
                            # Ajuste puede aumentar o disminuir, pero nunca negativo
                            # Limitar el ajuste para que no haga negativo el stock
                            max_decremento = min(10, cantidad_anterior)
                            ajuste = random.randint(-max_decremento, 10)
                            cantidad_nueva = max(0, cantidad_anterior + ajuste)
                        else:  # DEVOLUCION
                            # Devolución siempre aumenta el stock
                            cantidad_nueva = cantidad_anterior + cantidad
                        
                        # Asegurar que cantidad_nueva nunca sea negativa (PositiveIntegerField)
                        # Esto es redundante pero asegura que nunca falle
                        cantidad_nueva = max(0, int(cantidad_nueva))
                        
                        MovimientoStock.objects.create(
                            repuesto=repuesto,
                            tipo=tipo,
                            cantidad=cantidad,
                            cantidad_anterior=cantidad_anterior,
                            cantidad_nueva=cantidad_nueva,
                            motivo=fake.text(max_nb_chars=200),
                            usuario=random.choice(usuarios_stock),
                            ot=random.choice(ots) if ots and random.choice([True, False]) else None,
                            vehiculo=random.choice(vehiculos) if random.choice([True, False]) else None,
                        )
                        
                        cantidad_anterior = cantidad_nueva
                        stock.cantidad_actual = cantidad_nueva
                        stock.save()
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ Movimientos de stock creados\n'))

            # 10. CREAR SOLICITUDES DE REPUESTOS
            self.stdout.write('📋 Creando solicitudes de repuestos...')
            for ot in ots[:num_workorders//2]:
                # Crear solicitudes para algunos items de tipo REPUESTO
                items_repuesto = ot.items.filter(tipo='REPUESTO')[:2]
                for item in items_repuesto:
                    # Asignar un repuesto aleatorio a la solicitud
                    repuesto_solicitud = random.choice(repuestos) if repuestos else None
                    if repuesto_solicitud:
                        estado = random.choice(['PENDIENTE', 'APROBADA', 'RECHAZADA', 'ENTREGADA', 'CANCELADA'])
                        solicitante = ot.mecanico or random.choice(mecanicos) if mecanicos else None
                        
                        solicitud = SolicitudRepuesto.objects.create(
                            ot=ot,
                            item_ot=item,
                            repuesto=repuesto_solicitud,
                            cantidad_solicitada=item.cantidad,
                            cantidad_entregada=item.cantidad if estado == 'ENTREGADA' else 0,
                            estado=estado,
                            motivo=fake.text(max_nb_chars=200),
                            solicitante=solicitante,
                            aprobador=random.choice(jefes_taller) if jefes_taller and estado in ['APROBADA', 'ENTREGADA'] else None,
                            entregador=random.choice(usuarios_por_rol['ADMIN']) if usuarios_por_rol['ADMIN'] and estado == 'ENTREGADA' else None,
                            fecha_solicitud=fake.date_time_between(start_date=ot.apertura, end_date='now', tzinfo=timezone.get_current_timezone()),
                            fecha_aprobacion=fake.date_time_between(start_date=ot.apertura, end_date='now', tzinfo=timezone.get_current_timezone()) if estado in ['APROBADA', 'ENTREGADA'] else None,
                            fecha_entrega=fake.date_time_between(start_date=ot.apertura, end_date='now', tzinfo=timezone.get_current_timezone()) if estado == 'ENTREGADA' else None,
                        )
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ Solicitudes de repuestos creadas\n'))

            # 11. CREAR HISTORIAL DE REPUESTOS POR VEHÍCULO
            self.stdout.write('📊 Creando historial de repuestos por vehículo...')
            for vehiculo in vehiculos[:num_vehicles//2]:
                for _ in range(random.randint(2, 8)):
                    repuesto = random.choice(repuestos)
                    ot = random.choice(ots) if ots else None
                    item_ot = None
                    if ot:
                        items_repuesto = list(ot.items.filter(tipo='REPUESTO').all())
                        item_ot = random.choice(items_repuesto) if items_repuesto else None
                    
                    HistorialRepuestoVehiculo.objects.create(
                        vehiculo=vehiculo,
                        repuesto=repuesto,
                        cantidad=random.randint(1, 5),
                        ot=ot,
                        item_ot=item_ot,
                        costo_unitario=repuesto.precio_referencia,
                    )
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ Historial de repuestos creado\n'))

        self.stdout.write(self.style.SUCCESS('\n✅ ¡Datos de prueba generados exitosamente!\n'))
        self.stdout.write(self.style.SUCCESS('📊 Resumen:'))
        self.stdout.write(f'  - Superusuario Admin: admin (contraseña: admin123)')
        self.stdout.write(f'  - Usuarios adicionales: {num_users}')
        self.stdout.write(f'  - Vehículos: {num_vehicles}')
        self.stdout.write(f'  - Choferes: {num_drivers}')
        self.stdout.write(f'  - Órdenes de Trabajo: {num_workorders}')
        # self.stdout.write(f'  - Emergencias: {num_emergencies}')  # App eliminada
        self.stdout.write(f'  - Agendas: {num_agendas}')
        self.stdout.write(f'  - Repuestos: {num_repuestos}')
        self.stdout.write(f'  - Ingresos de vehículos: {len(ingresos)}')
        self.stdout.write('\n💡 Credenciales de acceso:')
        self.stdout.write('   - Superusuario: admin / admin123')
        self.stdout.write('   - Otros usuarios: [username] / password123\n')

