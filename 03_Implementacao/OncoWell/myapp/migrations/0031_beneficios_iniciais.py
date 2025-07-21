from django.db import migrations

def criar_beneficios(apps, schema_editor):
    Beneficio = apps.get_model('myapp', 'Beneficio')
    Beneficio.objects.create(
        titulo='Benefícios da escrita terapêutica',
        descricao='A escrita terapêutica ajuda a processar emoções, reduzir o stress e promover o autoconhecimento.'
    )
    Beneficio.objects.create(
        titulo='Conteúdos informativos de valor clínico',
        descricao='Acesso a informação validada por profissionais de saúde, relevante para o percurso oncológico.'
    )
    Beneficio.objects.create(
        titulo='Testemunhos genuínos de utilizadores',
        descricao='Partilha de experiências reais para inspirar e apoiar outros utilizadores.'
    )
    Beneficio.objects.create(
        titulo='Perguntas frequentes com respostas claras',
        descricao='Respostas diretas e acessíveis às dúvidas mais comuns sobre o cancro e o tratamento.'
    )
    Beneficio.objects.create(
        titulo='Espaço reservado para diálogo com profissionais',
        descricao='Possibilidade de comunicar diretamente com profissionais de saúde para esclarecimento de dúvidas.'
    )

def apagar_beneficios(apps, schema_editor):
    Beneficio = apps.get_model('myapp', 'Beneficio')
    Beneficio.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0030_merge_20250721_1549'),
    ]
    operations = [
        migrations.RunPython(criar_beneficios, apagar_beneficios),
    ] 