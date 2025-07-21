from myapp.models import Paciente, ProfissionalSaude

def user_type_flags(request):
    is_paciente = False
    is_profissional = False
    if request.user.is_authenticated:
        is_paciente = Paciente.objects.filter(id=request.user.id).exists()
        is_profissional = ProfissionalSaude.objects.filter(id=request.user.id).exists()
    return {
        'is_paciente': is_paciente,
        'is_profissional': is_profissional,
    } 