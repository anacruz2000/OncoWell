from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from myapp.models import Utilizador, Paciente, ProfissionalSaude, TopTestemunho, Hospital, JournPerguntas, JournRespostas
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Subquery
import random
import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date

# Create your views here.
def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Redirecionar profissionais de saúde para a página de pacientes
            try:
                ProfissionalSaude.objects.get(id=user.id)
                return redirect('inicio_psi')
            except ProfissionalSaude.DoesNotExist:
                return redirect('journaling')
        else:
            return render(request, 'login.html', {'error_message': 'Nome de utilizador ou palavra-passe inválidos'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def beneficios(request):
    return render(request, 'beneficios.html', {'current_page': 'beneficios'})

@csrf_exempt
def journaling(request):
    from myapp.models import JournPerguntas, JournRespostas, Utilizador
    import json
    today = datetime.today().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(7)]
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resposta_texto = data.get('resposta')
            data_resposta = data.get('data')
            privacidade = data.get('privacidade')
            pergunta_id = data.get('pergunta_id')
            if not (resposta_texto and data_resposta and privacidade and pergunta_id):
                return JsonResponse({'status': 'error', 'message': 'Dados em falta.'}, status=400)
            if not request.user.is_authenticated:
                return JsonResponse({'status': 'error', 'message': 'Precisa de login.'}, status=403)
            pergunta = JournPerguntas.objects.get(id=pergunta_id)
            JournRespostas.objects.create(
                utilizador=request.user,
                pergunta=pergunta,
                resposta_texto=resposta_texto
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # GET: lógica para associar pergunta ao dia/utilizador
    selected_date = request.GET.get('data')
    if not selected_date:
        selected_date = today.strftime('%Y-%m-%d')
    else:
        selected_date = parse_date(selected_date)
        if not selected_date:
            selected_date = today
    pergunta = None
    if request.user.is_authenticated:
        resposta_existente = JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=selected_date).first()
        if resposta_existente:
            pergunta = resposta_existente.pergunta
        else:
            # Buscar perguntas ainda não respondidas neste dia
            perguntas_respondidas_ids = JournRespostas.objects.filter(utilizador=request.user, data_resposta__date=selected_date).values_list('pergunta_id', flat=True)
            perguntas_disponiveis = JournPerguntas.objects.exclude(id__in=perguntas_respondidas_ids)
            perguntas = list(perguntas_disponiveis)
            pergunta = random.choice(perguntas) if perguntas else None
    else:
        perguntas = list(JournPerguntas.objects.all())
        pergunta = random.choice(perguntas) if perguntas else None
    return render(request, 'journaling.html', {
        'current_page': 'journaling',
        'last_7_days': last_7_days,
        'user_authenticated': request.user.is_authenticated,
        'pergunta': pergunta
    })

def informacoes(request):
    return render(request, 'informacoes.html', {'current_page': 'informacoes'})

def testemunhos(request):
    testemunhos = TopTestemunho.objects.order_by('-data')  # Ordenar por data decrescente (mais recentes primeiro)
    
    # Distribuir testemunhos alternadamente entre as páginas
    # para que os mais recentes apareçam no início de cada página
    page_left = []
    page_right = []
    
    for i, testemunho in enumerate(testemunhos):
        if i % 2 == 0:  # Índices pares (0, 2, 4, ...) vão para página esquerda
            page_left.append(testemunho)
        else:  # Índices ímpares (1, 3, 5, ...) vão para página direita
            page_right.append(testemunho)
    
    # Verificar se o usuário é um profissional de saúde
    is_professional = False
    if request.user.is_authenticated:
        try:
            ProfissionalSaude.objects.get(id=request.user.id)
            is_professional = True
        except ProfissionalSaude.DoesNotExist:
            is_professional = False
    
    return render(request, 'testemunhos.html', {
        'current_page': 'testemunhos',
        'page_left': page_left,
        'page_right': page_right,
        'is_professional': is_professional,
    })

def qa(request):
    return render(request, 'q&a.html', {'current_page': 'q&a'})

def chat(request):
    return render(request, 'chat.html')

def pacientes(request):
    return render(request, 'pacientes.html')

def inicio_psi(request):
    return render(request, 'inicio_psi.html', {'current_page': 'inicio_psi'})

def enviar_pergunta(request):
    if request.method == 'POST':
        pergunta = request.POST.get('pergunta')
        email = request.POST.get('email')
        
        # Exemplo: enviar para email
        send_mail(
            subject='Nova pergunta recebida',
            message=f'Pergunta: {pergunta}\nEmail: {email}',
            from_email='site@oncowell.pt',
            recipient_list=['equipa@oncowell.pt'],
        )

        return redirect('q&a')  # ou mostrar mensagem de sucesso

    return redirect('q&a')

def register_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        username = request.POST.get('username')
        email = request.POST.get('email')
        data_nascimento = request.POST.get('data_nascimento')
        password = request.POST.get('password')
        cancer_type = request.POST.get('cancer_type')
        hospital_id = request.POST.get('hospital')
        healthcare_type = request.POST.get('healthcare_type')
        medical_license = request.POST.get('medical_license')
        license_validity = request.POST.get('license_validity')

        if Utilizador.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error_message': 'Nome de utilizador já existe.'})
        if Utilizador.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error_message': 'Email já está registado.'})

        if not nome or not username or not email or not password:
            return render(request, 'register.html', {'error_message': 'Todos os campos obrigatórios devem ser preenchidos.'})

        if(len(cancer_type) > 0):
            print('paciente')
            # Buscar o hospital selecionado
            hospital = None
            if hospital_id and hospital_id != '':
                try:
                    hospital = Hospital.objects.get(id=hospital_id)
                except Hospital.DoesNotExist:
                    pass
            
            Paciente.objects.create_user(nome=nome, username=username, email=email, data_nascimento=data_nascimento, password=password, tipo_cancro=cancer_type, hospital=hospital, estado_pac='estavel')
        elif(len(healthcare_type) > 0):
            print('profissional')
            ProfissionalSaude.objects.create_user(nome=nome, username=username, email=email, password=password, data_nascimento=data_nascimento, tipo_profissional=healthcare_type, certificado_profissional=medical_license, validade_certificado=license_validity)
        else:
            user = Utilizador.objects.create_user(username=username, email=email, password=password, nome=nome, data_nascimento=data_nascimento)
            user.save()

        
        return redirect('login')
    
    # Criar hospitais se não existirem
    criar_hospitais_se_necessario()
    
    # Buscar lista de hospitais para o formulário
    hospitais = Hospital.objects.all().order_by('nome')
    
    # Buscar choices dos tipos de cancro
    tipos_cancro = Paciente.TIPOS_CANCRO_CHOICES
    
    return render(request, 'register.html', {
        'current_page': 'register',
        'hospitais': hospitais,
        'tipos_cancro': tipos_cancro,
    })

def criar_hospitais_se_necessario():
    """Cria os hospitais na base de dados se não existirem"""
    if Hospital.objects.count() == 0:
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
            Hospital.objects.get_or_create(nome=codigo, defaults={'morada': ''})
        print("Hospitais criados automaticamente!")

def journaling_delhes(request):
    return render(request, 'journaling_delhes.html', {'current_page': 'journaling_delhes'})

@csrf_exempt
def salvar_testemunho(request):
    print("DEBUG: View salvar_testemunho chamada")
    if request.method == 'POST':
        try:
            # Verificar se o usuário é um profissional de saúde
            if request.user.is_authenticated:
                try:
                    ProfissionalSaude.objects.get(id=request.user.id)
                    return JsonResponse({'status': 'error', 'message': 'Profissionais de saúde não podem criar testemunhos'}, status=403)
                except ProfissionalSaude.DoesNotExist:
                    pass  # Usuário não é profissional de saúde, pode continuar
            
            data = json.loads(request.body)
            print(f"DEBUG: Dados recebidos: {data}")
            titulo = data.get('titulo')
            texto = data.get('texto')
            visibilidade = data.get('visibilidade')
            autor = request.user if (visibilidade == 'publico' and request.user.is_authenticated) else None
            print(f"DEBUG: Criando testemunho - Título: {titulo}, Visibilidade: {visibilidade}, Autor: {autor}")
            testemunho = TopTestemunho.objects.create(
                titulo=titulo,
                texto=texto,
                visibilidade=visibilidade,
                autor=autor,
                data=date.today()
            )
            print(f"DEBUG: Testemunho criado com ID: {testemunho.id}")
            return JsonResponse({'status': 'ok', 'data': testemunho.data.strftime('%d/%m/%Y')})
        except Exception as e:
            print(f"DEBUG: Erro ao criar testemunho: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def lista_testemunhos(request):
    testemunhos = myapp_toptestemunhos.objects.all()  # Busca todos os users da base de dados
    return render(request, 'lista_testemunhos.html', {'testemunho': testemunhos})

@csrf_exempt
def editar_testemunho(request, testemunho_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            testemunho = TopTestemunho.objects.get(id=testemunho_id)
            
            # Verificar se o usuário é o autor do testemunho
            if testemunho.autor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Não autorizado'}, status=403)
            
            testemunho.titulo = data.get('titulo')
            testemunho.texto = data.get('texto')
            testemunho.visibilidade = data.get('visibilidade')
            testemunho.save()
            
            return JsonResponse({'status': 'ok'})
        except TopTestemunho.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Testemunho não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def apagar_testemunho(request, testemunho_id):
    if request.method == 'POST':
        try:
            testemunho = TopTestemunho.objects.get(id=testemunho_id)
            
            # Verificar se o usuário é o autor do testemunho
            if testemunho.autor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Não autorizado'}, status=403)
            
            testemunho.delete()
            return JsonResponse({'status': 'ok'})
        except TopTestemunho.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Testemunho não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@login_required
def meu_perfil(request):
    user = request.user
    
    # Verificar se é paciente ou profissional de saúde
    try:
        paciente = Paciente.objects.get(id=user.id)
        user_type = 'paciente'
        user_data = {
            'nome': paciente.nome,
            'email': paciente.email,
            'username': paciente.username,
            'data_nascimento': paciente.data_nascimento,
            'tipo_cancro': paciente.tipo_cancro,
            'tipo_cancro_choices': Paciente.TIPOS_CANCRO_CHOICES,
            'hospital': paciente.hospital,
            'estado_pac': paciente.estado_pac,
        }
    except Paciente.DoesNotExist:
        try:
            profissional = ProfissionalSaude.objects.get(id=user.id)
            user_type = 'profissional'
            user_data = {
                'nome': profissional.nome,
                'email': profissional.email,
                'username': profissional.username,
                'data_nascimento': profissional.data_nascimento,
                'tipo_profissional': profissional.tipo_profissional,
                'tipo_profissional_display': profissional.get_tipo_profissional_display(),
                'certificado_profissional': profissional.certificado_profissional,
                'validade_certificado': profissional.validade_certificado,
            }
        except ProfissionalSaude.DoesNotExist:
            user_type = 'utilizador'
            user_data = {
                'nome': user.nome,
                'email': user.email,
                'username': user.username,
                'data_nascimento': user.data_nascimento,
            }
    
    if request.method == 'POST':
        # Processar edição do perfil
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        data_nascimento = request.POST.get('data_nascimento')
        
        if nome and email:
            user.nome = nome
            user.email = email
            if data_nascimento:
                user.data_nascimento = data_nascimento
            user.save()
            
            # Atualizar campos específicos do tipo de usuário
            if user_type == 'paciente':
                paciente.tipo_cancro = request.POST.get('tipo_cancro', '')
                hospital_id = request.POST.get('hospital')
                if hospital_id and hospital_id != '':
                    try:
                        hospital = Hospital.objects.get(id=hospital_id)
                        paciente.hospital = hospital
                    except Hospital.DoesNotExist:
                        paciente.hospital = None
                else:
                    paciente.hospital = None
                paciente.save()
            elif user_type == 'profissional':
                profissional.tipo_profissional = request.POST.get('tipo_profissional', '')
                profissional.certificado_profissional = request.POST.get('certificado_profissional', '')
                if request.POST.get('validade_certificado'):
                    profissional.validade_certificado = request.POST.get('validade_certificado')
                profissional.save()
            
            return redirect('meu_perfil')
    
    # Criar hospitais se não existirem
    criar_hospitais_se_necessario()
    
    # Buscar lista de hospitais para o formulário
    hospitais = Hospital.objects.all().order_by('nome')
    
    return render(request, 'meu_perfil.html', {
        'current_page': 'meu_perfil',
        'user_type': user_type,
        'user_data': user_data,
        'hospitais': hospitais,
    })

@login_required
def apagar_conta(request):
    if request.method == 'POST':
        user = request.user
        
        # Verificar se o usuário confirmou a ação
        confirmacao = request.POST.get('confirmacao')
        if confirmacao == 'APAGAR':
            # Apagar o usuário (isso também apaga Paciente ou ProfissionalSaude automaticamente)
            user.delete()
            logout(request)
            messages.success(request, 'A sua conta foi apagada com sucesso.')
            return redirect('home')
        else:
            messages.error(request, 'Confirmação incorreta. A conta não foi apagada.')
            return redirect('meu_perfil')
    
    return redirect('meu_perfil')

def pergunta_aleatoria(request):
    user = request.user

    # Perguntas já respondidas por este user
    respondidas_ids = Resposta.objects.filter(user=user).values_list('pergunta_id', flat=True)

    # Perguntas ainda não respondidas
    perguntas_disponiveis = Pergunta.objects.exclude(id__in=Subquery(respondidas_ids))

    pergunta = None
    if perguntas_disponiveis.exists():
        pergunta = random.choice(list(perguntas_disponiveis))

    if request.method == 'POST' and pergunta:
        resposta_texto = request.POST.get('resposta')
        Resposta.objects.create(
            user=user,
            pergunta=pergunta,
            resposta_texto=resposta_texto
        )
        return redirect('pergunta_aleatoria')

    return render(request, 'pergunta.html', {'pergunta': pergunta})
