from django.core.management.base import BaseCommand
from myapp.models import Hospital

class Command(BaseCommand):
    help = 'Popula a base de dados com a lista de hospitais'

    def handle(self, *args, **options):
        hospitais = [
            ('CHULN', 'Centro Hospitalar Universitário Lisboa Norte'),
            ('CHULC', 'Centro Hospitalar Universitário Lisboa Central'),
            ('CHULSJ', 'Centro Hospitalar Universitário Lisboa Sul'),
            ('IPO_LISBOA', 'Instituto Português de Oncologia de Lisboa Francisco Gentil'),
            ('IPO_PORTO', 'Instituto Português de Oncologia do Porto Francisco Gentil'),
            ('IPO_COIMBRA', 'Instituto Português de Oncologia de Coimbra Francisco Gentil'),
            ('CHUC', 'Centro Hospitalar e Universitário de Coimbra'),
            ('CHP', 'Centro Hospitalar do Porto'),
            ('CHVNG', 'Centro Hospitalar Vila Nova de Gaia/Espinho'),
            ('CHTMAD', 'Centro Hospitalar Tâmega e Sousa'),
            ('CHTS', 'Centro Hospitalar Trás-os-Montes e Alto Douro'),
            ('CHBA', 'Centro Hospitalar do Baixo Alentejo'),
            ('CHAL', 'Centro Hospitalar do Algarve'),
            ('CHLC', 'Centro Hospitalar Leiria-Pombal'),
            ('CHBV', 'Centro Hospitalar Barreiro Montijo'),
            ('CHLO', 'Centro Hospitalar de Loures'),
            ('CHOEIRAS', 'Centro Hospitalar Oeste'),
            ('CHTM', 'Centro Hospitalar Tondela Viseu'),
            ('CHUCG', 'Centro Hospitalar Universitário Cova da Beira'),
            ('CHUCB', 'Centro Hospitalar Universitário do Algarve'),
            ('HOSPITAL_PRIVADO', 'Hospital Privado'),
            ('OUTRO', 'Outro'),
        ]

        for codigo, nome in hospitais:
            hospital, created = Hospital.objects.get_or_create(
                nome=codigo,
                defaults={'morada': ''}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Hospital criado: {nome}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Hospital já existe: {nome}')
                )

        self.stdout.write(
            self.style.SUCCESS('Processo de criação de hospitais concluído!')
        ) 