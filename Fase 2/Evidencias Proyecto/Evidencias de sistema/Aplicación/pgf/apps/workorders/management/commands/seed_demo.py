from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.vehicles.models import Vehiculo
from apps.users.models import Profile
from apps.workorders.models import (
    OrdenTrabajo, ItemOT, Presupuesto, DetallePresup,
    Aprobacion, Pausa, Checklist, Evidencia
)
from decimal import Decimal

class Command(BaseCommand):
    help = "Crea datos de demostración completos para PGF"

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write("Creando usuarios...")
        users_data = [
            ("admin", "admin@example.com", "ADMIN", "admin123", True, "Admin", "Sistema"),
            ("ejecutivo", "ejecutivo@example.com", "EJECUTIVO", "ejecutivo123", False, "Ejecutivo", "PepsiCo"),
            ("guardia", "guardia@example.com", "GUARDIA", "guardia123", False, "Guardia", "Seguridad"),
            ("mecanico1", "mecanico1@example.com", "MECANICO", "mecanico123", False, "Juan", "Pérez"),
            ("mecanico2", "mecanico2@example.com", "MECANICO", "mecanico123", False, "Carlos", "González"),
            ("supervisor", "supervisor@example.com", "SUPERVISOR", "supervisor123", True, "Supervisor", "Zona Norte"),
            ("jefe_taller", "jefe@example.com", "JEFE_TALLER", "jefe123", False, "Jefe", "Taller"),
            ("sponsor", "sponsor@example.com", "SPONSOR", "sponsor123", False, "Sponsor", "PepsiCo"),
            ("coordinador", "coordinador@example.com", "COORDINADOR_ZONA", "coord123", False, "Coordinador", "Zona"),
            ("recepcionista", "recepcionista@example.com", "RECEPCIONISTA", "recep123", False, "Recepcionista", "Taller"),
        ]
        
        created = {}
        mecanicos = []
        for username, email, rol, pwd, is_staff, first_name, last_name in users_data:
            u, created_user = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "rol": rol,
                    "is_staff": is_staff,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            u.set_password(pwd)
            u.save()
            
            # Guardar el primer usuario de cada rol
            if rol not in created:
                created[rol] = u
            
            # Guardar todos los mecánicos
            if rol == "MECANICO":
                mecanicos.append(u)
            
            # Asegurar que el usuario tenga perfil
            Profile.objects.get_or_create(
                user=u,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "notificaciones_email": True,
                    "notificaciones_sonido": True,
                    "notificaciones_push": False,
                }
            )
            
            # Si el usuario ya existía, actualizar el perfil
            if not created_user and hasattr(u, 'profile'):
                u.profile.first_name = first_name
                u.profile.last_name = last_name
                u.profile.save()

        self.stdout.write("Creando vehículos...")
        vehiculos_data = [
            ("ABCJ12", "Scania", "R500", 2021, "ACTIVO", "Norte"),
            ("KLMN34", "Volvo", "FH 460", 2022, "ACTIVO", "Norte"),
            ("PQRS56", "Mercedes", "Actros", 2020, "EN_MANTENIMIENTO", "Sur"),
            ("TUVW78", "Iveco", "Stralis", 2023, "ACTIVO", "Norte"),
            ("XYZA90", "MAN", "TGX", 2021, "EN_ESPERA", "Sur"),
            ("BCDE12", "Scania", "R450", 2022, "ACTIVO", "Centro"),
            ("FGHI34", "Volvo", "FH 500", 2023, "ACTIVO", "Norte"),
            ("JKLM56", "Mercedes", "Arocs", 2020, "ACTIVO", "Sur"),
        ]
        
        vehiculos = {}
        for patente, marca, modelo, anio, estado, zona in vehiculos_data:
            v, _ = Vehiculo.objects.get_or_create(
                patente=patente,
                defaults={
                    "marca": marca,
                    "modelo": modelo,
                    "anio": anio,
                    "vin": f"VIN{patente}",
                    "estado": estado,
                    "supervisor": created.get("SUPERVISOR"),
                    "tipo": "DIESEL",
                    "categoria": "REPARTO",
                }
            )
            vehiculos[patente] = v

        self.stdout.write("Creando órdenes de trabajo...")
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        hace_3_dias = hoy - timedelta(days=3)
        hace_7_dias = hoy - timedelta(days=7)
        hace_15_dias = hoy - timedelta(days=15)
        
        # OT en diferentes estados
        estados_ot = [
            ("ABIERTA", vehiculos["ABCJ12"], "Ruidos en frenos y vibración al frenar", ayer),
            ("EN_DIAGNOSTICO", vehiculos["KLMN34"], "Revisión de motor - pérdida de potencia", hoy),
            ("EN_EJECUCION", vehiculos["PQRS56"], "Cambio de aceite y filtros", hoy),
            ("EN_PAUSA", vehiculos["TUVW78"], "Reparación de sistema eléctrico", ayer),
            ("EN_QA", vehiculos["XYZA90"], "Mantención programada 20.000 km", hoy),
            ("CERRADA", vehiculos["BCDE12"], "Revisión de suspensión", hace_3_dias),
            ("CERRADA", vehiculos["FGHI34"], "Cambio de neumáticos", hace_7_dias),
            ("CERRADA", vehiculos["JKLM56"], "Reparación de sistema de frenos", hace_15_dias),
        ]
        
        ots = []
        for estado, vehiculo, motivo, fecha_apertura in estados_ot:
            ot, _ = OrdenTrabajo.objects.get_or_create(
                vehiculo=vehiculo,
                estado=estado,
                defaults={
                    "responsable": created.get("MECANICO") or created.get("SUPERVISOR"),
                    "supervisor": created.get("SUPERVISOR"),
                    "jefe_taller": created.get("JEFE_TALLER"),
                    "motivo": motivo,
                    "apertura": timezone.make_aware(timezone.datetime.combine(fecha_apertura, timezone.datetime.min.time())),
                }
            )
            
            # Si está cerrada, agregar fecha de cierre
            if estado == "CERRADA":
                fecha_cierre = fecha_apertura + timedelta(days=2)
                ot.cierre = timezone.make_aware(timezone.datetime.combine(fecha_cierre, timezone.datetime.min.time()))
                ot.diagnostico_final = "Trabajo completado exitosamente"
                ot.save()
            
            ots.append(ot)
            
            # Asignar mecánico a OT en ejecución
            if estado == "EN_EJECUCION" and mecanicos:
                ot.responsable = mecanicos[0]
                ot.save()
            
            # Agregar items a algunas OT
            if estado in ["ABIERTA", "EN_EJECUCION", "EN_QA"]:
                ItemOT.objects.get_or_create(
                    ot=ot,
                    descripcion="Diagnóstico general",
                    defaults={
                        "tipo": "SERVICIO",
                        "cantidad": 1,
                        "costo_unitario": Decimal("50.00")
                    }
                )
                
                if estado == "ABIERTA":
                    ItemOT.objects.get_or_create(
                        ot=ot,
                        descripcion="Pastillas de freno delanteras",
                        defaults={
                            "tipo": "REPUESTO",
                            "cantidad": 1,
                            "costo_unitario": Decimal("180.00")
                        }
                    )
                    ItemOT.objects.get_or_create(
                        ot=ot,
                        descripcion="Discos de freno delanteros (par)",
                        defaults={
                            "tipo": "REPUESTO",
                            "cantidad": 1,
                            "costo_unitario": Decimal("320.00")
                        }
                    )
                    ItemOT.objects.get_or_create(
                        ot=ot,
                        descripcion="Mano de obra",
                        defaults={
                            "tipo": "SERVICIO",
                            "cantidad": 4,
                            "costo_unitario": Decimal("25.00")
                        }
                    )
                    
                    # Crear presupuesto
                    total = sum([i.cantidad * i.costo_unitario for i in ot.items.all()])
                    pres, _ = Presupuesto.objects.get_or_create(
                        ot=ot,
                        defaults={
                            "total": total,
                            "requiere_aprobacion": True,
                            "umbral": Decimal("300.00")
                        }
                    )
                    for it in ot.items.all():
                        DetallePresup.objects.get_or_create(
                            presupuesto=pres,
                            concepto=it.descripcion,
                            defaults={
                                "cantidad": it.cantidad,
                                "precio": it.costo_unitario
                            }
                        )
                    Aprobacion.objects.get_or_create(
                        presupuesto=pres,
                        defaults={
                            "sponsor": created.get("SPONSOR"),
                            "estado": "PENDIENTE",
                            "comentario": "A la espera de confirmación"
                        }
                    )
            
            # Agregar checklist a OT cerradas y en QA
            if estado in ["CERRADA", "EN_QA"]:
                Checklist.objects.get_or_create(
                    ot=ot,
                    defaults={
                        "resultado": "OK" if estado == "CERRADA" else "PENDIENTE",
                        "observaciones": "Todo conforme." if estado == "CERRADA" else "En revisión."
                    }
                )
            
            # Agregar pausa a OT en pausa
            if estado == "EN_PAUSA" and mecanicos:
                Pausa.objects.get_or_create(
                    ot=ot,
                    usuario=mecanicos[0],
                    fin__isnull=True,
                    defaults={
                        "motivo": "Esperando repuestos",
                        "inicio": timezone.now() - timedelta(hours=2)
                    }
                )

        self.stdout.write(self.style.SUCCESS("\n✅ Datos de demostración creados exitosamente!\n"))
        self.stdout.write(self.style.SUCCESS("📋 Credenciales de acceso:\n"))
        self.stdout.write("   👤 admin / admin123 (Administrador)")
        self.stdout.write("   👤 ejecutivo / ejecutivo123 (Ejecutivo)")
        self.stdout.write("   👤 supervisor / supervisor123 (Supervisor)")
        self.stdout.write("   👤 jefe_taller / jefe123 (Jefe de Taller)")
        self.stdout.write("   👤 mecanico1 / mecanico123 (Mecánico)")
        self.stdout.write("   👤 guardia / guardia123 (Guardia)")
        self.stdout.write("   👤 sponsor / sponsor123 (Sponsor)")
        self.stdout.write("\n📊 Datos creados:")
        self.stdout.write(f"   • {len(created)} usuarios con perfiles")
        self.stdout.write(f"   • {len(vehiculos)} vehículos")
        self.stdout.write(f"   • {len(ots)} órdenes de trabajo en diferentes estados")
        self.stdout.write("\n🚀 Puedes iniciar sesión en http://localhost:3000")
