# Generated by Django 5.2 on 2025-07-13 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0026_alter_journrespostas_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journrespostas',
            name='data_resposta',
            field=models.DateTimeField(),
        ),
    ]
