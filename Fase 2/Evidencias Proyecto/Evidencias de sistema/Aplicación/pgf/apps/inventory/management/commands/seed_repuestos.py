"""
Comando para crear repuestos de prueba para el módulo de inventario.

Uso:
    python manage.py seed_repuestos
    python manage.py seed_repuestos --cantidad 20
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import Repuesto, Stock
import random

# Categorías comunes de repuestos
CATEGORIAS = [
    "Frenos",
    "Motor",
    "Transmisión",
    "Suspensión",
    "Eléctrico",
    "Neumáticos",
    "Filtros",
    "Aceites",
    "Baterías",
    "Luces",
]

# Marcas comunes
MARCAS = [
    "Bosch",
    "Delphi",
    "Denso",
    "NGK",
    "Mann",
    "Mobil",
    "Castrol",
    "Michelin",
    "Bridgestone",
    "ACDelco",
]

# Unidades de medida
UNIDADES = ["UNIDAD", "LITRO", "KILO", "METRO"]


class Command(BaseCommand):
    help = "Crea repuestos de prueba para el módulo de inventario"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cantidad",
            type=int,
            default=15,
            help="Cantidad de repuestos a crear (default: 15)",
        )

    def handle(self, *args, **options):
        cantidad = options["cantidad"]
        
        self.stdout.write(f"🔧 Creando {cantidad} repuestos de prueba...")
        
        repuestos_creados = 0
        
        for i in range(cantidad):
            categoria = random.choice(CATEGORIAS)
            marca = random.choice(MARCAS)
            unidad = random.choice(UNIDADES)
            
            # Generar código único
            codigo = f"{categoria[:3].upper()}-{marca[:3].upper()}-{i+1:03d}"
            
            # Verificar que el código no exista
            while Repuesto.objects.filter(codigo=codigo).exists():
                codigo = f"{categoria[:3].upper()}-{marca[:3].upper()}-{i+1:03d}-{random.randint(1, 999)}"
            
            # Generar nombre
            nombres_repuestos = {
                "Frenos": ["Pastillas de Freno", "Discos de Freno", "Líquido de Freno", "Cilindro de Freno"],
                "Motor": ["Filtro de Aceite", "Filtro de Aire", "Bujías", "Correa de Distribución"],
                "Transmisión": ["Aceite de Transmisión", "Filtro de Transmisión", "Junta de Transmisión"],
                "Suspensión": ["Amortiguadores", "Resortes", "Bujes", "Rótulas"],
                "Eléctrico": ["Batería", "Alternador", "Arranque", "Fusibles"],
                "Neumáticos": ["Neumático", "Válvula", "Balanceador"],
                "Filtros": ["Filtro de Aceite", "Filtro de Aire", "Filtro de Combustible", "Filtro de Cabina"],
                "Aceites": ["Aceite Motor", "Aceite Transmisión", "Aceite Diferencial"],
                "Baterías": ["Batería 12V", "Batería 24V", "Batería Seca"],
                "Luces": ["Foco H4", "Foco H7", "LED", "Intermitente"],
            }
            
            nombre_opciones = nombres_repuestos.get(categoria, ["Repuesto Genérico"])
            nombre = f"{random.choice(nombre_opciones)} {marca}"
            
            # Precio de referencia aleatorio
            precio = round(random.uniform(5000, 50000), 2)
            
            # Crear repuesto
            repuesto = Repuesto.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=f"Repuesto de {categoria} marca {marca}",
                marca=marca,
                categoria=categoria,
                precio_referencia=precio,
                unidad_medida=unidad,
                activo=True,
            )
            
            # Crear stock inicial
            cantidad_actual = random.randint(0, 50)
            cantidad_minima = random.randint(5, 15)
            ubicacion = f"Estante {random.randint(1, 10)}-{random.choice(['A', 'B', 'C', 'D'])}"
            
            Stock.objects.create(
                repuesto=repuesto,
                cantidad_actual=cantidad_actual,
                cantidad_minima=cantidad_minima,
                ubicacion=ubicacion,
            )
            
            repuestos_creados += 1
            
            self.stdout.write(
                f"  ✅ {codigo} - {nombre} (Stock: {cantidad_actual}, Mín: {cantidad_minima})"
            )
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(f"✅ {repuestos_creados} repuestos creados exitosamente!")
        )
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                "\n📦 Los repuestos están listos para usar en el módulo de inventario."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  Algunos repuestos tienen stock bajo el mínimo para probar las alertas."
            )
        )

