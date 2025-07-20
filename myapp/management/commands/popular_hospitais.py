from django.core.management.base import BaseCommand
from myapp.models import Hospital

# Mapeamento hospital -> zona (ajustar conforme necessário)
HOSPITAIS_ZONAS = {
    'CHULN': 'Lisboa',
    'CHULC': 'Lisboa',
    'CHULSJ': 'Lisboa',
    'IPO_LISBOA': 'Lisboa',
    'IPO_PORTO': 'Porto',
    'IPO_COIMBRA': 'Coimbra',
    'CHUC': 'Coimbra',
    'CHP': 'Porto',
    'CHVNG': 'Porto',
    'CHTMAD': 'Porto',
    'CHTS': 'Vila Real',
    'CHBA': 'Beja',
    'CHAL': 'Faro',
    'CHLC': 'Leiria',
    'CHBV': 'Setúbal',
    'CHLO': 'Lisboa',
    'CHOEIRAS': 'Lisboa',
    'CHTM': 'Viseu',
    'CHUCG': 'Castelo Branco',
    'CHUCB': 'Faro',
    'HOSPITAL_PRIVADO': 'Outro',
    'OUTRO': 'Outro',
}

class Command(BaseCommand):
    help = 'Preenche o campo zona dos hospitais existentes.'

    def handle(self, *args, **options):
        atualizados = 0
        for hospital in Hospital.objects.all():
            zona = HOSPITAIS_ZONAS.get(hospital.nome, 'Outro')
            if hospital.zona != zona:
                hospital.zona = zona
                hospital.save()
                atualizados += 1
        self.stdout.write(self.style.SUCCESS(f'Zonas preenchidas para {atualizados} hospitais.')) 