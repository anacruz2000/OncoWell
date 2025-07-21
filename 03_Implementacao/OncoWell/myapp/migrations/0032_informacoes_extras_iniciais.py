from django.db import migrations

def criar_informacoes_extras(apps, schema_editor):
    InformacaoExtra = apps.get_model('myapp', 'InformacaoExtra')
    InformacaoExtra.objects.create(
        titulo='Perucas: onde conseguir',
        descricao='Consulte o nosso mapa de locais para encontrar perucas e acessórios perto de si. Clique no botão para aceder ao mapa: https://www.google.com/maps/d/u/0/edit?mid=1IVjr_Xs8tk5RXsLPnG8kKsGTnkONgZ0&usp=sharing'
    )
    InformacaoExtra.objects.create(
        titulo='Ajuda no Transporte: Não Vá Sozinho',
        descricao='Precisa de ir ao hospital com frequência? Pode pedir transporte não urgente pelo SNS. Muitas câmaras municipais também ajudam com transporte gratuito – informe-se no centro de saúde ou junta de freguesia.'
    )
    InformacaoExtra.objects.create(
        titulo='Direitos no Trabalho',
        descricao='Está em tratamento e não pode trabalhar? Tem direito a baixa médica prolongada com subsídio de doença. Peça ajuda ao seu médico ou veja mais no site da Segurança Social.'
    )
    InformacaoExtra.objects.create(
        titulo='Apoio Financeiro',
        descricao='Subsídio de doença: Se está de baixa médica, pode receber apoio da Segurança Social.\n\nIsenção de taxas moderadoras: Doentes oncológicos estão isentos de pagar consultas e exames no SNS.\n\nApoios da Segurança Social ou da Câmara Municipal: Podem existir ajudas específicas para despesas como medicamentos, transportes ou alimentação. Fale com um assistente social.'
    )

def apagar_informacoes_extras(apps, schema_editor):
    InformacaoExtra = apps.get_model('myapp', 'InformacaoExtra')
    InformacaoExtra.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0031_beneficios_iniciais'),
    ]
    operations = [
        migrations.RunPython(criar_informacoes_extras, apagar_informacoes_extras),
    ] 