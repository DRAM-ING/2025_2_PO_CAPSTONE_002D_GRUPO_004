# Generated manually to increase rol max_length for new roles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_add_administrativo_bodega_roles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='rol',
            field=models.CharField(
                choices=[
                    ('GUARDIA', 'Guardia'),
                    ('MECANICO', 'Mecánico'),
                    ('SUPERVISOR', 'Supervisor Zonal'),
                    ('COORDINADOR_ZONA', 'Coordinador de Zona'),
                    ('RECEPCIONISTA', 'Recepcionista'),
                    ('JEFE_TALLER', 'Jefe de Taller'),
                    ('EJECUTIVO', 'Ejecutivo'),
                    ('SPONSOR', 'Sponsor'),
                    ('ADMIN', 'Administrador'),
                    ('CHOFER', 'Chofer'),
                    ('ADMINISTRATIVO_TALLER', 'Administrativo de Taller'),
                    ('BODEGA', 'Bodega / Encargado de Repuestos'),
                ],
                default='ADMIN',
                max_length=25
            ),
        ),
    ]

