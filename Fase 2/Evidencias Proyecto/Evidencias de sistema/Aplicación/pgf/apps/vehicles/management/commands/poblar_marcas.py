"""
Comando para poblar la tabla de marcas de vehículos con las marcas más comunes.

Uso:
    python manage.py poblar_marcas

Este comando crea las marcas de vehículos más comunes en Chile y a nivel internacional.
Si una marca ya existe, la actualiza marcándola como activa.
"""

from django.core.management.base import BaseCommand
from apps.vehicles.models import Marca


# Lista de marcas de vehículos comunes en Chile
MARCAS_COMUNES = [
    "Toyota",
    "Nissan",
    "Chevrolet",
    "Ford",
    "Hyundai",
    "Kia",
    "Mitsubishi",
    "Mazda",
    "Suzuki",
    "Volkswagen",
    "Peugeot",
    "Renault",
    "Fiat",
    "Citroën",
    "Mercedes-Benz",
    "BMW",
    "Audi",
    "Volvo",
    "Isuzu",
    "Hino",
    "Scania",
    "Volvo Trucks",
    "Iveco",
    "JAC",
    "Great Wall",
    "BYD",
    "Geely",
    "Chery",
    "Changan",
    "Dongfeng",
    "FAW",
    "DFSK",
    "MG",
    "Tata",
    "Mahindra",
    "RAM",
    "Jeep",
    "Dodge",
    "GMC",
    "Cadillac",
    "Lincoln",
    "Infiniti",
    "Lexus",
    "Acura",
    "Honda",
    "Subaru",
    "Mitsubishi Motors",
    "Suzuki Motor",
    "Opel",
    "Skoda",
    "Seat",
    "Alfa Romeo",
    "Ferrari",
    "Lamborghini",
    "Porsche",
    "Jaguar",
    "Land Rover",
    "Mini",
    "Smart",
    "Tesla",
]


class Command(BaseCommand):
    help = "Pobla la tabla de marcas con las marcas de vehículos más comunes"

    def handle(self, *args, **options):
        self.stdout.write("🚗 Poblando tabla de marcas de vehículos...\n")
        
        creadas = 0
        actualizadas = 0
        
        for nombre_marca in MARCAS_COMUNES:
            marca, created = Marca.objects.get_or_create(
                nombre=nombre_marca,
                defaults={"activa": True}
            )
            
            if created:
                creadas += 1
                self.stdout.write(f"  ✅ Creada: {nombre_marca}")
            else:
                # Si ya existe, asegurarse de que esté activa
                if not marca.activa:
                    marca.activa = True
                    marca.save()
                    actualizadas += 1
                    self.stdout.write(f"  🔄 Reactivada: {nombre_marca}")
        
        total = Marca.objects.filter(activa=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Proceso completado:\n"
                f"   - Marcas creadas: {creadas}\n"
                f"   - Marcas reactivadas: {actualizadas}\n"
                f"   - Total de marcas activas: {total}"
            )
        )

