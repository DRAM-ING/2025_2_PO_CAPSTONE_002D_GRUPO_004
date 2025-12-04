# Generated migration to update EMERGENCIA type to REPARACION
from django.db import migrations


def update_emergencia_to_reparacion(apps, schema_editor):
    """
    Actualiza todas las OTs con tipo EMERGENCIA a REPARACION.
    
    Esto es necesario porque la opción EMERGENCIA ha sido removida
    del sistema pero puede haber registros históricos con este tipo.
    """
    OrdenTrabajo = apps.get_model('workorders', 'OrdenTrabajo')
    
    # Contar cuántas OTs tienen tipo EMERGENCIA
    count = OrdenTrabajo.objects.filter(tipo='EMERGENCIA').count()
    
    if count > 0:
        # Actualizar todas las OTs con tipo EMERGENCIA a REPARACION
        OrdenTrabajo.objects.filter(tipo='EMERGENCIA').update(tipo='REPARACION')
        print(f"✅ Actualizadas {count} OTs de tipo EMERGENCIA a REPARACION")
    else:
        print("ℹ️  No se encontraron OTs con tipo EMERGENCIA")


def reverse_update(apps, schema_editor):
    """
    Función reversa: No hacemos nada porque no queremos volver a EMERGENCIA.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0016_remove_site_field'),
    ]

    operations = [
        migrations.RunPython(
            update_emergencia_to_reparacion,
            reverse_update,
        ),
    ]

