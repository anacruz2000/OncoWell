from django.core.management.base import BaseCommand
from myapp.models import ProfissionalSaude

class Command(BaseCommand):
    help = 'Atualiza o campo n_pacientes de todos os profissionais de saúde com base nos pacientes atualmente associados.'

    def handle(self, *args, **options):
        total = 0
        for profissional in ProfissionalSaude.objects.all():
            count = profissional.pacientes.count()
            profissional.n_pacientes = count
            profissional.save()
            self.stdout.write(self.style.SUCCESS(f'Profissional {profissional.nome} atualizado para {count} pacientes.'))
            total += 1
        self.stdout.write(self.style.SUCCESS(f'Total de profissionais atualizados: {total}')) 