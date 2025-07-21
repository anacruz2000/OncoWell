from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Hospital(models.Model):
    HOSPITAIS_CHOICES = [
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
    
    nome = models.CharField(max_length=100, choices=HOSPITAIS_CHOICES, unique=True)
    morada = models.CharField(max_length=255, blank=True, null=True)
    zona = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.get_nome_display()

    class Meta:
        verbose_name_plural = "Hospitais"

class Utilizador(AbstractUser):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    username = models.CharField(max_length=100, unique=True)
    data_nascimento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username

class Paciente(Utilizador):
    TIPOS_CANCRO_CHOICES = [
        ('MAMA', 'Cancro da Mama'),
        ('PULMAO', 'Cancro do Pulmão'),
        ('COLON', 'Cancro do Cólon/Recto'),
        ('PROSTATA', 'Cancro da Próstata'),
        ('PELE', 'Cancro da Pele (Melanoma)'),
        ('CERVICAL', 'Cancro do Colo do Útero'),
        ('OVARIO', 'Cancro do Ovário'),
        ('PANCREAS', 'Cancro do Pâncreas'),
        ('ESTOMAGO', 'Cancro do Estômago'),
        ('FIGADO', 'Cancro do Fígado'),
        ('CEREBRO', 'Cancro do Cérebro'),
        ('LEUCEMIA', 'Leucemia'),
        ('LINFOMA', 'Linfoma'),
        ('MULTIPLO_MIELOMA', 'Múltiplo Mieloma'),
        ('SARCOMA', 'Sarcoma'),
        ('OUTRO', 'Outro'),
    ]
    
    tipo_cancro = models.CharField(max_length=20, choices=TIPOS_CANCRO_CHOICES)
    outro_cancer_type = models.CharField(max_length=100, blank=True, null=True)  # Campo para especificar quando "OUTRO" é selecionado
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    outro_hospital = models.CharField(max_length=200, blank=True, null=True)  # Campo para especificar quando "Outro" é selecionado
    estado_pac = models.CharField(max_length=100)
    profissionais = models.ManyToManyField('ProfissionalSaude', related_name='pacientes')

    def __str__(self):
        return f"Paciente: {self.nome}"

class ProfissionalSaude(Utilizador):
    certificado_profissional = models.CharField(max_length=100)
    validade_certificado = models.DateField()
    tipo_profissional = models.CharField(max_length=20, choices=[
        ('PSICOLOGO', 'Psicólogo'),
        ('MEDICO', 'Médico'),
        ('ENFERMEIRO', 'Enfermeiro'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('AUSENTE', 'Ausente'),
    ], default='ONLINE')
    zona_trabalho = models.CharField(max_length=100, blank=True, null=True)
    especialidades = models.JSONField(default=list, blank=True)  # Lista de até 5 especialidades
    n_pacientes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_tipo_profissional_display()}: {self.nome}"

class Enfermidade(models.Model):
    nome = models.CharField(max_length=100)
    pacientes = models.ManyToManyField(Paciente, related_name='enfermidades')

    def __str__(self):
        return self.nome

class Conversa(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='conversas')
    profissional = models.ForeignKey(ProfissionalSaude, on_delete=models.CASCADE, related_name='conversas')
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_mensagem = models.DateTimeField(auto_now=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('paciente', 'profissional')

    def __str__(self):
        return f"Conversa entre {self.paciente.nome} e {self.profissional.nome}"

class MsgChatInd(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='mensagens', null=True, blank=True)
    emissor = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    receptor = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_recebidas')
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensagem de {self.emissor} para {self.receptor}"

class JournalItem(models.Model):
    utilizador = models.ForeignKey(Utilizador, on_delete=models.CASCADE)
    data = models.DateField()
    pergunta = models.TextField()
    conteudo = models.TextField()
    publico_npublico = models.BooleanField()

    def __str__(self):
        return f"Journal de {self.utilizador} em {self.data}"

class PergIndividual(models.Model):
    utilizador = models.ForeignKey(Utilizador, on_delete=models.CASCADE)
    conteudo = models.TextField()
    email = models.EmailField(null=True, blank=True)
    data_pergunta = models.DateField()
    publico_npublico = models.BooleanField()

    def __str__(self):
        return f"Pergunta de {self.utilizador} em {self.data_pergunta}"

class TopicFAQ(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class FAQ(models.Model):
    topic = models.ForeignKey(TopicFAQ, on_delete=models.CASCADE)
    pergunta = models.TextField()
    resposta = models.TextField()
    vezes_feita = models.IntegerField(default=5)

    def __str__(self):
        return self.pergunta

class TopicInf(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Informacao(models.Model):
    topic = models.ForeignKey(TopicInf, on_delete=models.CASCADE)
    conteudo = models.TextField()

    def __str__(self):
        return f"Informação sobre {self.topic}"

class TpPerg(models.Model):
    descricao = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)

    def __str__(self):
        return self.descricao

class BancoPerg(models.Model):
    conteudo = models.TextField()
    tipo = models.ForeignKey(TpPerg, on_delete=models.CASCADE)

    def __str__(self):
        return self.conteudo[:50]

class TopTestemunho(models.Model):
    titulo = models.CharField(max_length=200)
    texto = models.TextField()
    data = models.DateField(auto_now_add=True)
    visibilidade = models.CharField(max_length=10, choices=[('publico', 'Público'), ('anonimo', 'Anónimo')])
    autor = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.titulo} ({self.data})"

class JournPerguntas(models.Model):
    texto = models.TextField()

    def __str__(self):
        return self.texto

class JournRespostas(models.Model):
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(JournPerguntas, on_delete=models.CASCADE, null=True, blank=True)
    resposta_texto = models.TextField()
    data_resposta = models.DateTimeField()  # Removido auto_now_add temporariamente
    privacidade = models.CharField(max_length=10, choices=[('publico', 'Público'), ('anonimo', 'Privado')], default='anonimo')
    cor_manual = models.CharField(max_length=10, blank=True, null=True, choices=[('vermelho','Vermelho'),('amarelo','Amarelo'),('verde','Verde')])

    class Meta:
        unique_together = ('utilizador', 'pergunta', 'data_resposta')

class Favorito(models.Model):
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos')
    favorito = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritado_por')

    class Meta:
        unique_together = ('utilizador', 'favorito')

class PerguntaResposta(models.Model):
    pergunta = models.TextField()
    resposta = models.TextField()
    topico = models.CharField(max_length=100, default="Outro")
    vezes_feita = models.IntegerField(default=1)
    data = models.DateTimeField(auto_now_add=True)

class EstadoPaciente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historico_estados')
    estado = models.CharField(max_length=20, choices=[('critico','Crítico'),('moderado','Moderado'),('estavel','Estável')])
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.paciente.nome} - {self.estado} em {self.data.strftime('%Y-%m-%d %H:%M')}"

class Beneficio(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()

    def __str__(self):
        return self.titulo

class InformacaoExtra(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()

    def __str__(self):
        return self.titulo

class LocalPeruca(models.Model):
    nome = models.CharField(max_length=200)
    morada = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.nome

