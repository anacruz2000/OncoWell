from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from myapp.models import Utilizador, Paciente, ProfissionalSaude, TopTestemunho
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import date

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
            return redirect('journaling')
        else:
            return render(request, 'login.html', {'error_message': 'Nome de utilizador ou palavra-passe inválidos'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def beneficios(request):
    return render(request, 'beneficios.html', {'current_page': 'beneficios'})

def journaling(request):
    today = datetime.today().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(7)]
    return render(request, 'journaling.html', {
        'current_page': 'journaling',
        'last_7_days': last_7_days,
        'user_authenticated': request.user.is_authenticated
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
    return render(request, 'inicio_psi.html')

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
        hospital = request.POST.get('hospital')

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
            Paciente.objects.create_user(nome=nome, username=username, email=email, data_nascimento=data_nascimento, password=password, tipo_cancro=cancer_type, hospital=hospital, estado_pac='estavel')
        elif(len(healthcare_type) > 0):
            print('profissional')
            ProfissionalSaude.objects.create_user(nome=nome, username=username, email=email, password=password, data_nascimento=data_nascimento, tipo_profissional=healthcare_type, certificado_profissional=medical_license, validade_certificado=license_validity)
        else:
            user = Utilizador.objects.create_user(username=username, email=email, password=password, nome=nome, data_nascimento=data_nascimento)
            user.save()

        
        return redirect('login')
    return render(request, 'register.html')

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
