from django.contrib import admin
from .models import (
    Hospital, Utilizador, Paciente, ProfissionalSaude,
    Enfermidade, MsgChatInd, JournalItem, PergIndividual,
    TopicFAQ, FAQ, TopicInf, Informacao, TpPerg, BancoPerg
)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['nome', 'morada']

@admin.register(Utilizador)
class UtilizadorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'username', 'email', 'data_nascimento', 'password']

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'username', 'data_nascimento', 'estado_pac']
    filter_horizontal = ['profissionais']

@admin.register(ProfissionalSaude)
class ProfissionalSaudeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'username', 'tipo_profissional', 'certificado_profissional', 'validade_certificado']

@admin.register(Enfermidade)
class EnfermidadeAdmin(admin.ModelAdmin):
    list_display = ['nome']
    filter_horizontal = ['pacientes']

@admin.register(MsgChatInd)
class MsgChatIndAdmin(admin.ModelAdmin):
    list_display = ['emissor', 'receptor', 'data']

@admin.register(JournalItem)
class JournalItemAdmin(admin.ModelAdmin):
    list_display = ['utilizador', 'data', 'publico_npublico']

@admin.register(PergIndividual)
class PergIndividualAdmin(admin.ModelAdmin):
    list_display = ['utilizador', 'data_pergunta', 'publico_npublico', 'email']

@admin.register(TopicFAQ)
class TopicFAQAdmin(admin.ModelAdmin):
    list_display = ['nome']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['topic', 'pergunta']

@admin.register(TopicInf)
class TopicInfAdmin(admin.ModelAdmin):
    list_display = ['nome']

@admin.register(Informacao)
class InformacaoAdmin(admin.ModelAdmin):
    list_display = ['topic']

@admin.register(TpPerg)
class TpPergAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'tipo']

@admin.register(BancoPerg)
class BancoPergAdmin(admin.ModelAdmin):
    list_display = ['conteudo', 'tipo']
