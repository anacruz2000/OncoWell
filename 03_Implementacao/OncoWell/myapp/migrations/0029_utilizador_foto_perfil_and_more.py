# Generated by Django 5.2 on 2025-07-16 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0028_alter_journrespostas_data_resposta'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilizador',
            name='foto_perfil',
            field=models.ImageField(blank=True, null=True, upload_to='fotos_perfil/'),
        ),
        migrations.AlterField(
            model_name='journrespostas',
            name='data_resposta',
            field=models.DateTimeField(),
        ),
    ]
