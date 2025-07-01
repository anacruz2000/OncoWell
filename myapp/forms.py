from django import forms
from .models import (
    Utilizador, Paciente, ProfissionalSaude, Enfermidade,
    Chat, Journaling, PergIndividual, MeuJournaling
)

class UtilizadorForm(forms.ModelForm):
    class Meta:
        model = Utilizador
        fields = ['nome', 'email', 'username', 'telemovel', 'password', 'data_nascimento']

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['utilizador', 'data_nascimento', 'estado_pac']

class ProfissionalForm(forms.ModelForm):
    class Meta:
        model = ProfissionalSaude
        fields = ['utilizador', 'tipo_profissional', 'certificado_profissional', 'validade_certificado', 'data_nascimento']

class EnfermidadeForm(forms.ModelForm):
    class Meta:
        model = Enfermidade
        fields = ['nome']

class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ['remetente', 'destinatario', 'conteudo']

class MeuJournalingForm(forms.ModelForm):
    class Meta:
        model = MeuJournaling
        fields = ['utilizador', 'data', 'texto_livre', 'pergunta_diaria', 'publico_npublico']

class PergIndividualForm(forms.ModelForm):
    class Meta:
        model = PergIndividual
        fields = ['faqs', 'conteudo', 'email', 'data_pergunta']
