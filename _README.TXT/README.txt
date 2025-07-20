# OncoWell

OncoWell é uma plataforma web desenvolvida em Django para apoio a pacientes oncológicos e profissionais de saúde, promovendo o acompanhamento, registo de sintomas, comunicação e partilha de informação.

## Funcionalidades Principais
- **Registo e autenticação** de pacientes e profissionais de saúde
- **Journaling**: registo diário de sintomas, emoções e reflexões, com avaliação automática de risco
- **Chat** entre pacientes e profissionais de saúde
- **Testemunhos**: partilha de experiências de pacientes
- **FAQ e Q&A**: perguntas frequentes e respostas automáticas
- **Gestão de perfil** para pacientes e profissionais
- **Atribuição automática** de profissionais a pacientes conforme zona e especialidade
- **Avaliação do estado do paciente** baseada nas respostas do journaling

## Estrutura do Projeto
- `myapp/`: aplicação principal com modelos, views, templates e static files
- `mysite/`: configuração do projeto Django
- `manage.py`: utilitário de gestão Django
- `requirements.txt`: dependências do projeto
- `Procfile`: configuração para deploy (ex: Render, Heroku)

## Requisitos
- Python 3.10+
- PostgreSQL (ou SQLite para testes locais)
- As dependências listadas em `requirements.txt`

## Instalação
1. Clone o repositório e aceda à pasta `03_Implementaçao`:
   ```bash
   git clone <repo-url>
   cd 03_Implementaçao
   ```
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate    # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure a base de dados em `mysite/settings.py` (por padrão usa PostgreSQL remoto; pode alterar para SQLite para testes):
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }
   ```
5. Aplique as migrações:
   ```bash
   python manage.py migrate
   ```
6. (Opcional) Crie um superuser:
   ```bash
   python manage.py createsuperuser
   ```
7. Inicie o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```

## Deploy
- O projeto está preparado para deploy em plataformas como Render ou Heroku.
- O ficheiro `Procfile` indica o comando de arranque:
  ```
  web: gunicorn OncoWell.wsgi
  ```
- Recomenda-se configurar variáveis de ambiente para as credenciais da base de dados e `SECRET_KEY` em produção.

## Modelos Principais
- **Utilizador** (herda de `AbstractUser`): base para pacientes e profissionais
- **Paciente**: tipo de cancro, hospital, estado, profissionais atribuídos
- **ProfissionalSaude**: tipo, especialidades, zona de trabalho, pacientes
- **Hospital**: lista de hospitais e zonas
- **JournPerguntas/JournRespostas**: perguntas e respostas de journaling
- **Conversa/MsgChatInd**: chat individual
- **TopTestemunho**: testemunhos públicos/privados
- **FAQ/PerguntaResposta**: perguntas frequentes e respostas

## Notas
- O projeto inclui scripts de gestão para popular hospitais e perguntas de journaling.
- O sistema de avaliação automática de respostas usa LLM (ver `server.py`).
- Para dúvidas, consulte os ficheiros de código ou contacte a equipa de desenvolvimento. 