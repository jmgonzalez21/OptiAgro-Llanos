from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red', '0003_modelo_costos'),
    ]

    operations = [
        migrations.AddField(
            model_name='ruta',
            name='distancia_fuente',
            field=models.CharField(
                choices=[('carretera', 'Por carretera (OSRM/OpenStreetMap)'), ('estimada', 'Estimada (línea recta x 1,3)'), ('manual', 'Ingresada manualmente')],
                default='manual', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='ruta',
            name='trayecto',
            field=models.JSONField(blank=True, help_text='GeoJSON LineString del trayecto por carretera (caché; [lon, lat]).', null=True),
        ),
    ]
