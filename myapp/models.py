from django.db import models

class Hospital(models.Model):
    nome = models.CharField(max_length=100)
    morada = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

class Utilizador(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    username = models.CharField(max_length=100, unique=True)
    telemovel = models.CharField(max_length=15)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    def __str__(self):
        return self.username

class Paciente(Utilizador):
    data_nascimento = models.DateField()
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

    def __str__(self):
        return f"{self.get_tipo_profissional_display()}: {self.nome}"

class Enfermidade(models.Model):
    nome = models.CharField(max_length=100)
    pacientes = models.ManyToManyField(Paciente, related_name='enfermidades')

    def __str__(self):
        return self.nome

class MsgChatInd(models.Model):
    emissor = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    receptor = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_recebidas')
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

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
