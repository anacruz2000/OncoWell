# Generated by Django 5.2 on 2025-07-02 17:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_rename_pergunta_journperguntas_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journrespostas',
            name='pergunta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='myapp.journperguntas'),
        ),
    ]
