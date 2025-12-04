"""
Comando para poblar la base de datos con datos de demostración.

Este comando crea:
- Vehículos (si no existen)
- Órdenes de Trabajo en diferentes estados
- Items de OT
- Presupuestos y aprobaciones
- Pausas
- Checklists
- Comentarios

NO crea usuarios (se asume que ya existen).
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from apps.vehicles.models import Vehiculo, Marca
from apps.workorders.models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
    Aprobacion, Pausa, Checklist, ComentarioOT
)
from apps.inventory.models import Repuesto


class Command(BaseCommand):
    help = "Pobla la base de datos con datos de demostración (sin crear usuarios)"

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Obtener usuarios existentes por rol
        self.stdout.write("Obteniendo usuarios existentes...")
        usuarios = {
            "ADMIN": User.objects.filter(rol="ADMIN").first(),
            "JEFE_TALLER": User.objects.filter(rol="JEFE_TALLER").first(),
            "SUPERVISOR": User.objects.filter(rol="SUPERVISOR").first(),
            "MECANICO": list(User.objects.filter(rol="MECANICO")[:3]),
            "GUARDIA": User.objects.filter(rol="GUARDIA").first(),
            "EJECUTIVO": User.objects.filter(rol="EJECUTIVO").first(),
            "SPONSOR": User.objects.filter(rol="SPONSOR").first(),
            "COORDINADOR_ZONA": User.objects.filter(rol="COORDINADOR_ZONA").first(),
        }
        
        # Verificar que existan usuarios mínimos
        if not usuarios["JEFE_TALLER"]:
            self.stdout.write(self.style.ERROR("❌ No se encontró usuario JEFE_TALLER. Se necesita al menos uno."))
            return
        if not usuarios["SUPERVISOR"]:
            self.stdout.write(self.style.ERROR("❌ No se encontró usuario SUPERVISOR. Se necesita al menos uno."))
            return
        if not usuarios["MECANICO"]:
            self.stdout.write(self.style.ERROR("❌ No se encontraron usuarios MECANICO. Se necesita al menos uno."))
            return
        
        self.stdout.write(f"✅ Usuarios encontrados: {len([u for u in usuarios.values() if u])} roles")
        
        # Crear marcas si no existen
        self.stdout.write("\n📦 Creando marcas de vehículos...")
        marcas_data = ["Scania", "Volvo", "Mercedes", "Iveco", "MAN", "Ford", "Chevrolet"]
        marcas = {}
        for nombre_marca in marcas_data:
            marca, _ = Marca.objects.get_or_create(
                nombre=nombre_marca,
                defaults={"activa": True}
            )
            marcas[nombre_marca] = marca
            self.stdout.write(f"   ✓ {nombre_marca}")
        
        # Crear vehículos si no existen suficientes
        self.stdout.write("\n🚗 Creando vehículos...")
        vehiculos_data = [
            ("ABCJ12", "Scania", "R500", 2021, "ACTIVO", "Norte"),
            ("KLMN34", "Volvo", "FH 460", 2022, "ACTIVO", "Norte"),
            ("PQRS56", "Mercedes", "Actros", 2020, "EN_MANTENIMIENTO", "Sur"),
            ("TUVW78", "Iveco", "Stralis", 2023, "ACTIVO", "Norte"),
            ("XYZA90", "MAN", "TGX", 2021, "EN_ESPERA", "Sur"),
            ("BCDE12", "Scania", "R450", 2022, "ACTIVO", "Centro"),
            ("FGHI34", "Volvo", "FH 500", 2023, "ACTIVO", "Norte"),
            ("JKLM56", "Mercedes", "Arocs", 2020, "ACTIVO", "Sur"),
            ("MNOP78", "Iveco", "Hi-Way", 2021, "ACTIVO", "Centro"),
            ("QRST90", "MAN", "TGS", 2022, "ACTIVO", "Norte"),
            ("UVWX12", "Ford", "F-350", 2023, "ACTIVO", "Sur"),
            ("YZAB34", "Chevrolet", "Silverado", 2021, "ACTIVO", "Centro"),
        ]
        
        vehiculos = {}
        for patente, marca_nombre, modelo, anio, estado, zona in vehiculos_data:
            marca = marcas.get(marca_nombre)
            if not marca:
                continue
                
            vehiculo, created = Vehiculo.objects.get_or_create(
                patente=patente,
                defaults={
                    "marca": marca,
                    "modelo": modelo,
                    "anio": anio,
                    "vin": f"VIN{patente}",
                    "estado": estado,
                    "supervisor": usuarios["SUPERVISOR"],
                    "tipo": "DIESEL",
                    "categoria": "REPARTO",
                    "zona": zona,
                    "kilometraje_actual": random.randint(50000, 200000),
                }
            )
            vehiculos[patente] = vehiculo
            if created:
                self.stdout.write(f"   ✓ {patente} - {marca_nombre} {modelo}")
        
        # Obtener repuestos existentes (si hay)
        repuestos = list(Repuesto.objects.filter(activo=True)[:10])
        
        # Crear OTs según especificación
        self.stdout.write("\n📋 Creando Órdenes de Trabajo...")
        
        hoy = timezone.now()
        ayer = hoy - timedelta(days=1)
        hace_3_dias = hoy - timedelta(days=3)
        hace_5_dias = hoy - timedelta(days=5)
        hace_7_dias = hoy - timedelta(days=7)
        
        # 5 OTs ABIERTAS
        ots_abiertas = []
        vehiculos_abiertas = list(vehiculos.values())[:5]
        motivos_abiertas = [
            "Ruidos en frenos y vibración al frenar",
            "Revisión de sistema eléctrico - luces intermitentes",
            "Pérdida de potencia del motor",
            "Revisión de suspensión - ruidos extraños",
            "Mantención preventiva 50.000 km",
        ]
        
        for i, (vehiculo, motivo) in enumerate(zip(vehiculos_abiertas, motivos_abiertas)):
            fecha_apertura = ayer - timedelta(days=i)
            ot = OrdenTrabajo.objects.create(
                vehiculo=vehiculo,
                estado="ABIERTA",
                tipo="MANTENCION" if i < 2 else "REPARACION",
                prioridad="ALTA" if i < 2 else "MEDIA",
                motivo=motivo,
                responsable=usuarios["JEFE_TALLER"],
                supervisor=usuarios["SUPERVISOR"],
                jefe_taller=usuarios["JEFE_TALLER"],
                apertura=fecha_apertura,
            )
            ots_abiertas.append(ot)
            self.stdout.write(f"   ✓ OT {str(ot.id)[:8]} - ABIERTA - {vehiculo.patente}")
        
        # 3 OTs EN_EJECUCION
        ots_ejecucion = []
        vehiculos_ejecucion = list(vehiculos.values())[5:8]
        motivos_ejecucion = [
            "Cambio de aceite y filtros",
            "Reparación de sistema de frenos",
            "Reemplazo de correa de distribución",
        ]
        mecanicos = usuarios["MECANICO"]
        
        for i, (vehiculo, motivo) in enumerate(zip(vehiculos_ejecucion, motivos_ejecucion)):
            fecha_apertura = hace_3_dias - timedelta(days=i)
            mecanico = mecanicos[i % len(mecanicos)] if mecanicos else usuarios["MECANICO"][0]
            
            ot = OrdenTrabajo.objects.create(
                vehiculo=vehiculo,
                estado="EN_EJECUCION",
                tipo="MANTENCION" if i == 0 else "REPARACION",
                prioridad="MEDIA",
                motivo=motivo,
                responsable=mecanico,
                supervisor=usuarios["SUPERVISOR"],
                jefe_taller=usuarios["JEFE_TALLER"],
                mecanico=mecanico,
                apertura=fecha_apertura,
                fecha_inicio_ejecucion=fecha_apertura + timedelta(days=1),
            )
            ots_ejecucion.append(ot)
            self.stdout.write(f"   ✓ OT {str(ot.id)[:8]} - EN_EJECUCION - {vehiculo.patente} (Mecánico: {mecanico.username})")
        
        # 1 OT CERRADA
        vehiculo_cerrada = list(vehiculos.values())[8] if len(vehiculos) > 8 else list(vehiculos.values())[0]
        fecha_apertura_cerrada = hace_7_dias
        fecha_cierre_cerrada = hace_5_dias
        
        ot_cerrada = OrdenTrabajo.objects.create(
            vehiculo=vehiculo_cerrada,
            estado="CERRADA",
            tipo="MANTENCION",
            prioridad="BAJA",
            motivo="Mantención preventiva 30.000 km",
            responsable=usuarios["JEFE_TALLER"],
            supervisor=usuarios["SUPERVISOR"],
            jefe_taller=usuarios["JEFE_TALLER"],
            mecanico=mecanicos[0] if mecanicos else None,
            apertura=fecha_apertura_cerrada,
            fecha_inicio_ejecucion=fecha_apertura_cerrada + timedelta(days=1),
            cierre=fecha_cierre_cerrada,
        )
        self.stdout.write(f"   ✓ OT {str(ot_cerrada.id)[:8]} - CERRADA - {vehiculo_cerrada.patente}")
        
        # 3 OTs EN_QA
        ots_qa = []
        vehiculos_qa = list(vehiculos.values())[9:12] if len(vehiculos) > 9 else list(vehiculos.values())[:3]
        motivos_qa = [
            "Reparación de sistema de transmisión",
            "Reemplazo de componentes del motor",
            "Mantención mayor 100.000 km",
        ]
        
        for i, (vehiculo, motivo) in enumerate(zip(vehiculos_qa, motivos_qa)):
            fecha_apertura = hace_5_dias - timedelta(days=i)
            mecanico = mecanicos[i % len(mecanicos)] if mecanicos else usuarios["MECANICO"][0]
            
            ot = OrdenTrabajo.objects.create(
                vehiculo=vehiculo,
                estado="EN_QA",
                tipo="REPARACION",
                prioridad="ALTA" if i == 0 else "MEDIA",
                motivo=motivo,
                responsable=usuarios["JEFE_TALLER"],
                supervisor=usuarios["SUPERVISOR"],
                jefe_taller=usuarios["JEFE_TALLER"],
                mecanico=mecanico,
                apertura=fecha_apertura,
                fecha_inicio_ejecucion=fecha_apertura + timedelta(days=1),
                fecha_diagnostico=fecha_apertura + timedelta(hours=2),
            )
            ots_qa.append(ot)
            self.stdout.write(f"   ✓ OT {str(ot.id)[:8]} - EN_QA - {vehiculo.patente}")
        
        # Crear items para las OTs
        self.stdout.write("\n🔧 Creando items de OT...")
        
        # Items para OTs ABIERTAS
        for ot in ots_abiertas:
            # Item de servicio (diagnóstico)
            ItemOT.objects.create(
                ot=ot,
                tipo="SERVICIO",
                descripcion="Diagnóstico general del vehículo",
                cantidad=1,
                costo_unitario=Decimal("50.00"),
            )
            
            # Items de repuestos (si hay repuestos disponibles)
            if repuestos and len(repuestos) > 0:
                repuesto = random.choice(repuestos)
                ItemOT.objects.create(
                    ot=ot,
                    tipo="REPUESTO",
                    descripcion=repuesto.nombre,
                    cantidad=random.randint(1, 3),
                    costo_unitario=repuesto.precio_referencia or Decimal("100.00"),
                    repuesto=repuesto,
                )
            
            # Item de servicio (mano de obra)
            ItemOT.objects.create(
                ot=ot,
                tipo="SERVICIO",
                descripcion="Mano de obra especializada",
                cantidad=random.randint(2, 6),
                costo_unitario=Decimal("25.00"),
            )
            self.stdout.write(f"   ✓ 3 items creados para OT {str(ot.id)[:8]}")
        
        # Items para OTs EN_EJECUCION
        for ot in ots_ejecucion:
            ItemOT.objects.create(
                ot=ot,
                tipo="SERVICIO",
                descripcion="Trabajo de reparación",
                cantidad=random.randint(4, 8),
                costo_unitario=Decimal("30.00"),
            )
            
            if repuestos and len(repuestos) > 0:
                repuesto = random.choice(repuestos)
                ItemOT.objects.create(
                    ot=ot,
                    tipo="REPUESTO",
                    descripcion=repuesto.nombre,
                    cantidad=random.randint(1, 2),
                    costo_unitario=repuesto.precio_referencia or Decimal("150.00"),
                    repuesto=repuesto,
                )
            self.stdout.write(f"   ✓ Items creados para OT {str(ot.id)[:8]}")
        
        # Items para OT CERRADA
        ItemOT.objects.create(
            ot=ot_cerrada,
            tipo="SERVICIO",
            descripcion="Mantención preventiva completa",
            cantidad=4,
            costo_unitario=Decimal("35.00"),
        )
        if repuestos and len(repuestos) > 0:
            repuesto = random.choice(repuestos)
            ItemOT.objects.create(
                ot=ot_cerrada,
                tipo="REPUESTO",
                descripcion=repuesto.nombre,
                cantidad=1,
                costo_unitario=repuesto.precio_referencia or Decimal("80.00"),
                repuesto=repuesto,
            )
        self.stdout.write(f"   ✓ Items creados para OT {str(ot_cerrada.id)[:8]}")
        
        # Items para OTs EN_QA
        for ot in ots_qa:
            ItemOT.objects.create(
                ot=ot,
                tipo="SERVICIO",
                descripcion="Trabajo de reparación mayor",
                cantidad=random.randint(6, 10),
                costo_unitario=Decimal("40.00"),
            )
            
            if repuestos and len(repuestos) > 0:
                for _ in range(random.randint(1, 3)):
                    repuesto = random.choice(repuestos)
                    ItemOT.objects.create(
                        ot=ot,
                        tipo="REPUESTO",
                        descripcion=repuesto.nombre,
                        cantidad=random.randint(1, 2),
                        costo_unitario=repuesto.precio_referencia or Decimal("200.00"),
                        repuesto=repuesto,
                    )
            self.stdout.write(f"   ✓ Items creados para OT {str(ot.id)[:8]}")
        
        # Crear presupuestos para algunas OTs
        self.stdout.write("\n💰 Creando presupuestos...")
        
        for ot in ots_abiertas[:3]:  # Solo para las primeras 3 OTs abiertas
            total_items = sum([item.cantidad * item.costo_unitario for item in ot.items.all()])
            if total_items > 0:
                presupuesto, _ = Presupuesto.objects.get_or_create(
                    ot=ot,
                    defaults={
                        "total": total_items,
                        "requiere_aprobacion": total_items > Decimal("300.00"),
                        "umbral": Decimal("300.00"),
                    }
                )
                
                # Crear detalles del presupuesto
                for item in ot.items.all():
                    DetallePresup.objects.get_or_create(
                        presupuesto=presupuesto,
                        concepto=item.descripcion,
                        defaults={
                            "cantidad": item.cantidad,
                            "precio": item.costo_unitario,
                        }
                    )
                
                # Crear aprobación si requiere
                if presupuesto.requiere_aprobacion and usuarios["SPONSOR"]:
                    Aprobacion.objects.get_or_create(
                        presupuesto=presupuesto,
                        defaults={
                            "sponsor": usuarios["SPONSOR"],
                            "estado": "PENDIENTE",
                            "comentario": "Esperando aprobación del sponsor",
                        }
                    )
                    self.stdout.write(f"   ✓ Presupuesto con aprobación pendiente para OT {str(ot.id)[:8]}")
                else:
                    self.stdout.write(f"   ✓ Presupuesto creado para OT {str(ot.id)[:8]}")
        
        # Crear pausas para OTs en ejecución
        self.stdout.write("\n⏸️  Creando pausas...")
        
        for ot in ots_ejecucion[:2]:  # Solo para las primeras 2
            if ot.mecanico:
                Pausa.objects.create(
                    ot=ot,
                    usuario=ot.mecanico,
                    motivo="Esperando repuestos",
                    inicio=timezone.now() - timedelta(hours=2),
                )
                self.stdout.write(f"   ✓ Pausa creada para OT {str(ot.id)[:8]}")
        
        # Crear checklists para OTs en QA y cerrada
        self.stdout.write("\n✅ Creando checklists...")
        
        for ot in ots_qa:
            Checklist.objects.create(
                ot=ot,
                verificador=usuarios["JEFE_TALLER"],
                resultado="PENDIENTE",
                observaciones="En proceso de verificación de calidad",
            )
            self.stdout.write(f"   ✓ Checklist creado para OT {str(ot.id)[:8]}")
        
        # Checklist para OT cerrada
        Checklist.objects.create(
            ot=ot_cerrada,
            verificador=usuarios["JEFE_TALLER"],
            resultado="OK",
            observaciones="Trabajo completado exitosamente. Todos los puntos verificados.",
        )
        self.stdout.write(f"   ✓ Checklist creado para OT {str(ot_cerrada.id)[:8]}")
        
        # Crear comentarios en algunas OTs
        self.stdout.write("\n💬 Creando comentarios...")
        
        comentarios_data = [
            (ots_abiertas[0], usuarios["SUPERVISOR"], "Necesitamos revisar el presupuesto antes de continuar"),
            (ots_ejecucion[0], ots_ejecucion[0].mecanico, "Repuestos ordenados, llegada estimada mañana"),
            (ots_qa[0], usuarios["JEFE_TALLER"], "Verificación de calidad en proceso"),
        ]
        
        for ot, usuario, texto in comentarios_data:
            if usuario:
                ComentarioOT.objects.create(
                    ot=ot,
                    usuario=usuario,
                    contenido=texto,
                )
                self.stdout.write(f"   ✓ Comentario creado para OT {str(ot.id)[:8]}")
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("✅ DATOS POBLADOS EXITOSAMENTE"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(f"\n📊 Resumen de datos creados:")
        self.stdout.write(f"   • {len(vehiculos)} vehículos")
        self.stdout.write(f"   • {len(ots_abiertas)} OTs ABIERTAS")
        self.stdout.write(f"   • {len(ots_ejecucion)} OTs EN_EJECUCION")
        self.stdout.write(f"   • 1 OT CERRADA")
        self.stdout.write(f"   • {len(ots_qa)} OTs EN_QA")
        self.stdout.write(f"   • {ItemOT.objects.count()} items de OT")
        self.stdout.write(f"   • {Presupuesto.objects.count()} presupuestos")
        self.stdout.write(f"   • {Pausa.objects.count()} pausas")
        self.stdout.write(f"   • {Checklist.objects.count()} checklists")
        self.stdout.write(f"   • {ComentarioOT.objects.count()} comentarios")
        self.stdout.write(self.style.SUCCESS("\n🚀 Los datos están listos para usar!"))

