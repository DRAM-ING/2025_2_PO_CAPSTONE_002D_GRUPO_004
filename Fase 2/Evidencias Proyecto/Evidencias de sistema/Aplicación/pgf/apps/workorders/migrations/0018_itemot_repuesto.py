# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('workorders', '0017_update_emergencia_to_reparacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemot',
            name='repuesto',
            field=models.ForeignKey(
                blank=True,
                help_text='Repuesto asociado a este item (solo si tipo es REPUESTO)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items_ot',
                to='inventory.repuesto'
            ),
        ),
    ]

