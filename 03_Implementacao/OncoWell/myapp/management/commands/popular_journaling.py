from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import Utilizador, JournPerguntas, JournRespostas
import random
from datetime import timedelta
import re

# Mapear temas para respostas genéricas
THEME_ANSWERS = {
    'leves': [
        "Hoje acordei com esperança e vontade de aproveitar o dia.",
        "Senti gratidão pelas pequenas coisas que me rodeiam.",
        "O meu corpo pediu descanso e respeitei esse pedido.",
        "Um sorriso inesperado tornou meu dia melhor.",
        "A música trouxe leveza ao meu coração hoje.",
        "Notei beleza nas pequenas rotinas do meu dia.",
        "A paz veio num momento de silêncio e respiração profunda.",
        "A cor do meu dia foi azul, de tranquilidade.",
        "O carinho de alguém me fez sentir amado(a).",
        "Hoje celebrei pequenas vitórias pessoais."
    ],
    'intermedias': [
        "Esta semana senti emoções intensas, mas consegui expressá-las.",
        "O apoio dos outros tem feito diferença no meu tratamento.",
        "Tenho permitido sentir e processar as minhas emoções.",
        "A vulnerabilidade trouxe conexão com quem me ouve.",
        "O medo aparece, mas tento enfrentá-lo com coragem.",
        "A expectativa dos outros pesa, mas procuro ser honesto(a) comigo.",
        "Recebi palavras que me confortaram num momento difícil.",
        "A solidão às vezes dói, mas procuro pedir ajuda.",
        "A paciência tem sido testada, mas aprendo a cada dia.",
        "A força emocional vem das memórias e do apoio de quem amo."
    ],
    'profundas': [
        "O diagnóstico mudou minha visão sobre o que é realmente importante.",
        "Descobri forças em mim que desconhecia.",
        "Quero deixar um legado de amor e resiliência.",
        "A esperança tornou-se essencial na minha jornada.",
        "Aprendi a viver com mais intenção e autenticidade.",
        "A dor trouxe compaixão e crescimento interior.",
        "O tempo ganhou um novo significado para mim.",
        "A espiritualidade tem sido fonte de conforto.",
        "Quero ser lembrado(a) pela coragem e pelo amor.",
        "A maior transformação foi aprender a aceitar e a seguir em frente."
    ]
}

# Palavras-chave para identificar o grupo da pergunta
THEME_KEYWORDS = [
    ("leves", [
        "acordar", "sorrir", "tranquila", "conforto", "grato", "música", "energia", "respirei", "ritual", "coisa", "corpo", "refeição", "cor", "paz", "hábito", "leveza", "atividade", "bonito", "descanso", "rotinas", "dormir", "sorrir", "prazer", "energia", "presente", "palavras", "alegria", "memória", "sozinho", "gratidão", "foco", "casa", "amado", "humor", "difícil", "carinho", "silêncio", "relaxa", "cheiros", "entusiasmo", "vitórias", "eu", "repetir", "bonito", "toque", "frase", "suficiente" ]),
    ("intermedias", [
        "emocionalmente", "expressar", "compreendido", "emoção", "tratamento", "medo", "atitudes", "dor", "conversar", "emoção", "palavras", "vulnerável", "expectativa", "culpa", "pesa", "cuidem", "seguro", "entendessem", "incerteza", "honesto", "forte", "apoio", "pensamento", "relações", "magoado", "conexão", "escondo", "ajuda", "coragem", "julgamento", "pedir", "força", "chorei", "vergonha", "processar", "emocionou", "paciência", "julgado", "valorizado", "mudanças", "visto", "emocionalmente", "escutar", "solidão", "fecho", "lado", "decepcionar", "fonte", "acolhido" ]),
    ("profundas", [
        "diagnóstico", "doença", "sentido", "legado", "sonhos", "invencível", "forte", "lembrado", "valores", "medos", "viver bem", "tempo", "floresceram", "sofrimento", "esperança", "pessoas", "capítulos", "propósito", "imagem", "emocional", "existência", "sucesso", "carta", "espiritual", "realizar", "mensagem", "cura", "transformação", "impactar", "crenças", "vivo", "futuro", "história", "aprendizagens", "amor", "resiliente", "intenção", "silêncio", "usar o tempo", "espiritualidade", "autenticidade", "sabedoria", "mistério", "essencial" ])
]

REFLEXOES_LIVRES = [
    "Acredito que cada dia traz uma nova oportunidade de crescer.",
    "Às vezes, o silêncio é a melhor resposta para o caos.",
    "Estou a aprender a valorizar o presente.",
    "A gratidão transforma a forma como vejo o mundo.",
    "Mesmo nos dias difíceis, há sempre algo positivo.",
    "A partilha de sentimentos ajuda a aliviar o peso.",
    "A esperança é o que me faz continuar.",
    "A minha força está nas pequenas vitórias.",
    "Permito-me sentir e aceitar as minhas emoções.",
    "A jornada é tão importante quanto o destino."
]

def identificar_tema(pergunta_texto):
    texto = pergunta_texto.lower()
    for tema, keywords in THEME_KEYWORDS:
        for kw in keywords:
            if re.search(rf"\\b{re.escape(kw)}\\b", texto):
                return tema
    return 'leves'  # padrão caso não encontre

class Command(BaseCommand):
    help = 'Popula respostas automáticas de journaling para todos os utilizadores.'

    def handle(self, *args, **options):
        utilizadores = Utilizador.objects.all()
        perguntas = list(JournPerguntas.objects.all())
        dias = 10  # agora cobre os últimos 10 dias
        respostas_por_dia = 1  # garantir pelo menos uma resposta por dia
        privacidades = ['publico', 'anonimo']
        hoje = timezone.now().date()
        reflexoes_adicionadas = 0
        reflexoes_total = 10
        reflexoes_livres = REFLEXOES_LIVRES.copy()
        random.shuffle(reflexoes_livres)

        for utilizador in utilizadores:
            for dia_offset in range(dias):
                data = hoje - timedelta(days=dia_offset)
                data_aware = timezone.make_aware(timezone.datetime.combine(data, timezone.datetime.min.time()))
                n_respostas = random.randint(2, 3)
                perguntas_disponiveis = perguntas.copy()
                for i in range(n_respostas):
                    # Aleatoriamente decide se será reflexão livre ou resposta a pergunta
                    if perguntas_disponiveis and (random.random() > 0.3 or not reflexoes_livres):
                        pergunta = random.choice(perguntas_disponiveis)
                        perguntas_disponiveis.remove(pergunta)
                        tema = identificar_tema(pergunta.texto)
                        resposta_texto = random.choice(THEME_ANSWERS[tema])
                        privacidade = privacidades[(dia_offset + i) % 2]
                        JournRespostas.objects.create(
                            utilizador=utilizador,
                            pergunta=pergunta,
                            resposta_texto=resposta_texto,
                            data_resposta=data_aware,
                            privacidade=privacidade
                        )
                        print(f'Criada resposta para {utilizador} no dia {data} para a pergunta: {pergunta.texto}')
                    elif reflexoes_livres:
                        JournRespostas.objects.create(
                            utilizador=utilizador,
                            pergunta=None,
                            resposta_texto=reflexoes_livres.pop(),
                            data_resposta=data_aware,
                            privacidade=privacidades[(dia_offset + i) % 2]
                        )
                        print(f'Criada reflexão livre para {utilizador} no dia {data}')
        self.stdout.write(self.style.SUCCESS('Respostas de journaling e reflexões livres populadas com sucesso!')) 