from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import Paciente, ProfissionalSaude, Conversa, MsgChatInd
import random

TEMAS_SAUDE_CANCRO = [
    "Como tem lidado com os efeitos do tratamento?",
    "Quais estratégias usa para manter o otimismo?",
    "Já experimentou algum grupo de apoio?",
    "Como comunica com a sua equipa médica?",
    "Tem dúvidas sobre algum sintoma recente?",
    "Como lida com o medo da recaída?",
    "Que conselhos daria a quem está a começar o tratamento?",
    "Como a família tem apoiado nesta fase?",
    "O que mudou na sua rotina desde o diagnóstico?",
    "Quais são as maiores dificuldades do dia a dia?",
    "Como se informa sobre o seu tipo de cancro?",
    "Já pensou em procurar uma segunda opinião médica?",
    "Como gere o stress relacionado com a doença?",
    "Que hábitos de saúde considera mais importantes?",
    "Como lida com os efeitos secundários dos medicamentos?",
]

RESPOSTAS_SAUDE_CANCRO = [
    "Procuro manter uma atitude positiva e conversar com outros pacientes ajuda bastante.",
    "Apoio da família e amigos tem sido fundamental para mim.",
    "Faço caminhadas e tento manter uma alimentação equilibrada.",
    "Sempre que tenho dúvidas, falo com o meu médico ou enfermeiro.",
    "Participo em grupos online e isso tem-me ajudado a sentir-me menos sozinho(a).",
    "O medo existe, mas tento focar-me nas pequenas vitórias diárias.",
    "A partilha de experiências com outros pacientes é muito enriquecedora.",
    "A informação correta é essencial para tomar boas decisões.",
    "A rotina mudou muito, mas aprendi a valorizar o presente.",
    "O apoio psicológico tem sido importante para gerir a ansiedade.",
]

class Command(BaseCommand):
    help = 'Gera conversas e mensagens entre todos os pacientes e profissionais de saúde, com temas de saúde e cancro.'

    def handle(self, *args, **options):
        pacientes = list(Paciente.objects.all())
        profissionais = list(ProfissionalSaude.objects.all())
        n_msgs = 5  # número de mensagens por conversa
        conversas_criadas = 0
        mensagens_criadas = 0
        agora = timezone.now()

        for paciente in pacientes:
            for profissional in profissionais:
                # Evitar duplicados devido ao unique_together
                conversa, created = Conversa.objects.get_or_create(
                    paciente=paciente,
                    profissional=profissional,
                    defaults={"ativa": True}
                )
                if created:
                    conversas_criadas += 1
                # Gerar mensagens alternadas
                ultimo_emissor = random.choice([paciente, profissional])
                for i in range(n_msgs):
                    if i % 2 == 0:
                        emissor = ultimo_emissor
                        receptor = profissional if emissor == paciente else paciente
                        conteudo = random.choice(TEMAS_SAUDE_CANCRO)
                    else:
                        emissor = receptor
                        receptor = ultimo_emissor
                        conteudo = random.choice(RESPOSTAS_SAUDE_CANCRO)
                    MsgChatInd.objects.create(
                        conversa=conversa,
                        emissor=emissor,
                        receptor=receptor,
                        conteudo=conteudo,
                        data=agora - timezone.timedelta(minutes=5*(n_msgs-i)),
                        lida=random.choice([True, False])
                    )
                    mensagens_criadas += 1
        self.stdout.write(self.style.SUCCESS(f'Foram criadas {conversas_criadas} conversas e {mensagens_criadas} mensagens entre pacientes e profissionais.')) 