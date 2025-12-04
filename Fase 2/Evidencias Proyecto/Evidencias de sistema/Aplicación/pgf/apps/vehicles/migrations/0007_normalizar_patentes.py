# Generated migration to normalize existing license plates

from django.db import migrations
import re


def normalizar_patentes(apps, schema_editor):
    """
    Normaliza todas las patentes existentes al formato estándar:
    - Sin guiones
    - Sin espacios
    - Mayúsculas
    """
    Vehiculo = apps.get_model('vehicles', 'Vehiculo')
    
    # Obtener todos los vehículos
    vehiculos = Vehiculo.objects.all()
    
    actualizados = 0
    errores = []
    
    for vehiculo in vehiculos:
        patente_original = vehiculo.patente
        
        # Normalizar: quitar espacios, guiones, guiones bajos y convertir a mayúsculas
        patente_normalizada = patente_original.replace(" ", "").replace("-", "").replace("_", "").upper()
        
        # Validar que tenga 6 caracteres después de normalizar
        if len(patente_normalizada) == 6:
            # Verificar que no exista otro vehículo con la misma patente normalizada
            # (excepto el actual)
            existe_duplicado = Vehiculo.objects.filter(
                patente=patente_normalizada
            ).exclude(pk=vehiculo.pk).exists()
            
            if not existe_duplicado:
                # Solo actualizar si cambió
                if patente_normalizada != patente_original:
                    vehiculo.patente = patente_normalizada
                    vehiculo.save(update_fields=['patente'])
                    actualizados += 1
            else:
                errores.append(f"Patente duplicada después de normalizar: {patente_original} → {patente_normalizada}")
        else:
            errores.append(f"Patente con longitud inválida después de normalizar: {patente_original} → {patente_normalizada} ({len(patente_normalizada)} caracteres)")
    
    # Imprimir resultados
    print(f"\n✅ Patentes normalizadas: {actualizados}")
    if errores:
        print(f"⚠️  Errores encontrados: {len(errores)}")
        for error in errores[:10]:  # Mostrar solo los primeros 10
            print(f"   - {error}")
        if len(errores) > 10:
            print(f"   ... y {len(errores) - 10} más")


def revertir_normalizacion(apps, schema_editor):
    """
    Esta función no puede revertir la normalización porque no tenemos
    el formato original guardado. Simplemente no hace nada.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0006_ingresovehiculo_fecha_salida_and_more'),
    ]

    operations = [
        migrations.RunPython(normalizar_patentes, revertir_normalizacion),
    ]

