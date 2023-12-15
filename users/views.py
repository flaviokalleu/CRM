from django.http import Http404
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
import json
from decimal import Decimal
from django.core.paginator import Paginator
from django.views.decorators.clickjacking import xframe_options_exempt
from django import template
from .forms import ProprietarioForm
from .serializers import ClienteSerializer
import requests
from .models import Cliente, Corretores, OpcaoProcesso, Processo, Proprietario, CustomUser, TipoProcesso, OpcaoSelecionada
from .forms import OpcoesForm
import shutil
from django.http import HttpResponse
from PyPDF2 import DocumentInformation, PdfReader, PdfWriter
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CorretorForm, ClienteForm, CorrespondenteForm, TransactionForm, DocumentoForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from .models import Cliente, Corretores, Correspondente, Transaction, FixedExpense, Documento
from django.db import models
from datetime import datetime
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
from django.views.decorators.http import require_POST
import fitz
from .models import NotaPrivada
from .models import VendaCorretor
from .models import Nota
import re
from django.conf import settings
from django.forms import inlineformset_factory
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import os
import base64
import json
from django.core.serializers import serialize
from .consulta import consulta_cpf_func
from django.http import HttpRequest
from .forms import UserSettingsForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
import requests
from django.db.models import F
# Importando o modelo UserAccessLog que você deve ter definido anteriormente
from .models import UserAccessLog
from django.shortcuts import render
from datetime import timedelta
from .models import Proprietario, Contato
from django.utils import timezone
from datetime import date
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core.serializers import serialize
from django.shortcuts import render, redirect
import calendar
from django.db.models import Count
from django.utils.translation import gettext as _


def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_location_from_ip(ip: str) -> str:
    try:
        # Usando um serviço gratuito para pegar a localização pelo IP
        response = requests.get(f'https://ipapi.co/{ip}/json/')
        data = response.json()
        return f"{data.get('city')}, {data.get('region')}, {data.get('country_name')}"
    except Exception as e:
        return 'Unknown location'


def redirect_to_dashboard(request):
    # Substitua pelo caminho adequado para o painel de controle em seu aplicativo
    return HttpResponseRedirect('/admin_dashboard/')


def login_view(request):
    # Se o usuário já estiver autenticado, redirecione para o dashboard
    if request.user.is_authenticated:
        return redirect_to_dashboard(request)

    # Se a solicitação for um POST, processar o formulário de login
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            ip = get_client_ip(request)
            location = get_location_from_ip(ip)
            browser_info = request.headers.get('User-Agent')

            UserAccessLog.objects.create(
                user=user,
                ip_address=ip,
                location=location,
                browser_info=browser_info,
                action='User logged in'
            )

            return redirect_to_dashboard(request)
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def is_corretor(user):
    return user.groups.filter(name='Corretores').exists()


def is_correspondent(user):
    return user.groups.filter(name='correspondente').exists()


def is_admin(user):
    return user.is_superuser


def redirect_to_dashboard(request):
    if request.user.is_superuser:
        return HttpResponseRedirect(reverse('admin_dashboard'))
    elif request.user.groups.filter(name='Corretores').exists():
        return HttpResponseRedirect(reverse('broker_dashboard'))
    elif request.user.groups.filter(name='correspondente').exists():
        return HttpResponseRedirect(reverse('correspondent_dashboard'))
    else:
        # Se não houver um redirecionamento específico para o tipo de usuário, redirecione para a página inicial
        return redirect_to_dashboard(request)


@login_required
@user_passes_test(is_corretor)
def broker_dashboard(request):
    # Coleta de dados
    fixed_expenses = get_fixed_expenses(request.user)
    dias = [i for i in range(1, 32)]

    despesas = Transaction.objects.filter(tipo='DESPESA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    receitas = Transaction.objects.filter(tipo='RECEITA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    total_receitas = Transaction.objects.filter(
        user=request.user, tipo='RECEITA').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas = Transaction.objects.filter(
        user=request.user, tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    saldo = receitas - despesas

    # Obter a contagem de vários modelos
    total_corretores = Corretores.objects.count()
    total_clientes = Cliente.objects.count()
    total_correspondentes = Correspondente.objects.count()
    recent_transactions = Transaction.objects.all().order_by('-id')[:8]

    total_proprietarios = Proprietario.objects.count()
    total_contatos = Contato.objects.count()
    contatos_hoje = Contato.objects.filter(
        data_registro=datetime.now().date()).count()
    contatos_7_dias = Contato.objects.filter(
        data_registro__gte=datetime.now() - timedelta(days=7)).count()

    status_counts = Cliente.objects.values(
        'status').annotate(total=Count('status'))
    status_counts_dict = {item['status']: item['total']
                          for item in status_counts}
    all_statuses = [
        {'status': choice[0], 'total': status_counts_dict.get(
            choice[0], 0), 'display': choice[1]}
        for choice in Cliente.STATUS_CHOICES
    ]

    # Converta STATUS_CHOICES em um dicionário para fácil acesso
    status_dict = dict(Cliente.STATUS_CHOICES)

    # Gerar dados mensais
    monthly_counts = Cliente.objects.filter(data_de_criacao__isnull=False).annotate(
        month=ExtractMonth('data_de_criacao'),
        year=ExtractYear('data_de_criacao')
    ).values('month', 'year').annotate(total=Count('id')).order_by('year', 'month')

    # Gerar dados anuais
    annual_counts = Cliente.objects.filter(data_de_criacao__isnull=False).annotate(
        year=ExtractYear('data_de_criacao')
    ).values('year').annotate(total=Count('id')).order_by('year')

    # Converter os QuerySets em JSON
    monthly_data_json = json.dumps(list(monthly_counts))
    annual_data_json = json.dumps(list(annual_counts))

# Mapeia o número do mês para o nome do mês
    months = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    # Corrige os rótulos do gráfico
    chart_labels = []
    for entry in monthly_counts:
        month = entry.get('month')
        year = entry.get('year')
        if month and month in months:
            chart_labels.append(f"{months[month]} {year}")
        else:
            chart_labels.append(f"Mês Desconhecido {year if year else ''}")

    chart_data = {
        'labels': chart_labels,
        'data': [entry.get('total', 0) for entry in monthly_counts]
    }

    chart_data_json = json.dumps(chart_data)

    today = datetime.now().day
    expenses_due_soon = [expense for expense in fixed_expenses if 0 < (
        expense.due_day - today) <= 3]

    current_year = datetime.now().year
    last_year = current_year - 1
    current_month = datetime.now().month

    total_current = Cliente.objects.filter(
        data_de_criacao__year=current_year,
        data_de_criacao__month=current_month
    ).count()
    total_last_year = Cliente.objects.filter(
        data_de_criacao__year=last_year,
        data_de_criacao__month=current_month
    ).count()

    try:
        percent_change = (
            (total_current - total_last_year) / total_last_year) * 100
    except ZeroDivisionError:
        percent_change = 0

    vendas_corretores = VendaCorretor.objects.all().order_by('-id')

   # Calcula os top 4 status
    top_statuses_data = Cliente.objects.values('status').annotate(
        total=Count('status')).order_by('-total')[:4]

    top_statuses = [
        {
            'status': item['status'],
            'total': item['total'],
            'display': Cliente(status=item['status']).get_status_display()
        }
        for item in top_statuses_data
    ]

    clientes = Cliente.objects.all()

    processos = Processo.objects.all().order_by('-data_inicio')
    processos_em_andamento = [
        processo for processo in processos if processo.data_finalizacao is None]
    total_processos_em_andamento = len(processos_em_andamento)

    try:
        corretor_group = Group.objects.get(name='Corretores')
        corretores = corretor_group.user_set.all()
    except Group.DoesNotExist:
        corretores = []

    # Calcular o progresso para cada processo
    for processo in processos:
        processo.progresso = calcular_progresso(
            processo, processo.id, processo.cliente)

    data_referencia = datetime.now() - timedelta(days=7)
    total_clientes_recentes = Cliente.objects.filter(
        data_de_criacao__gte=data_referencia).count()

    context = {
        'total_clientes_recentes': total_clientes_recentes,
        'total_processos_em_andamento': total_processos_em_andamento,
        'current_year': current_year,
        'current_month': current_month,
        'percent_change': int(percent_change),
        'monthly_data_json': monthly_data_json,
        'annual_data_json': annual_data_json,
        'chart_data_json': chart_data_json,
        'chart_data': chart_data,
        'expenses_due_soon': expenses_due_soon,
        'total_proprietarios': total_proprietarios,
        'total_contatos': total_contatos,
        'contatos_hoje': contatos_hoje,
        'contatos_7_dias': contatos_7_dias,
        'recent_transactions': recent_transactions,
        'total_corretores': total_corretores,
        'total_clientes': total_clientes,
        'total_correspondentes': total_correspondentes,
        'saldo': saldo,
        'despesas': despesas,
        'receitas': receitas,
        'fixed_expenses': fixed_expenses,
        'dias': dias,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'notas_privadas': NotaPrivada.objects.filter(user=request.user).order_by('-data'),
        'all_statuses': all_statuses,
        'username': request.user.username,
        'vendas_corretores': vendas_corretores,
        'top_statuses': top_statuses,
        'status_choices': dict(Cliente.STATUS_CHOICES),
        'clientes': clientes,
        'processos': processos,
    }

    return render(request, 'broker_dashboard.html', context)


@user_passes_test(is_correspondent)
@login_required
def correspondent_dashboard(request):
    # Coleta de dados
    fixed_expenses = get_fixed_expenses(request.user)
    dias = [i for i in range(1, 32)]

    despesas = Transaction.objects.filter(tipo='DESPESA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    receitas = Transaction.objects.filter(tipo='RECEITA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    total_receitas = Transaction.objects.filter(
        user=request.user, tipo='RECEITA').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas = Transaction.objects.filter(
        user=request.user, tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    saldo = receitas - despesas

    # Obter a contagem de vários modelos
    total_corretores = Corretores.objects.count()
    total_clientes = Cliente.objects.count()
    total_correspondentes = Correspondente.objects.count()
    recent_transactions = Transaction.objects.all().order_by('-id')[:8]

    total_proprietarios = Proprietario.objects.count()
    total_contatos = Contato.objects.count()
    contatos_hoje = Contato.objects.filter(
        data_registro=datetime.now().date()).count()
    contatos_7_dias = Contato.objects.filter(
        data_registro__gte=datetime.now() - timedelta(days=7)).count()

    status_counts = Cliente.objects.values(
        'status').annotate(total=Count('status'))
    status_counts_dict = {item['status']: item['total']
                          for item in status_counts}
    all_statuses = [
        {'status': choice[0], 'total': status_counts_dict.get(
            choice[0], 0), 'display': choice[1]}
        for choice in Cliente.STATUS_CHOICES
    ]

    # Converta STATUS_CHOICES em um dicionário para fácil acesso
    status_dict = dict(Cliente.STATUS_CHOICES)

    # Gerar dados mensais
    monthly_counts = Cliente.objects.filter(data_de_criacao__isnull=False).annotate(
        month=ExtractMonth('data_de_criacao'),
        year=ExtractYear('data_de_criacao')
    ).values('month', 'year').annotate(total=Count('id')).order_by('year', 'month')

    # Gerar dados anuais
    annual_counts = Cliente.objects.filter(data_de_criacao__isnull=False).annotate(
        year=ExtractYear('data_de_criacao')
    ).values('year').annotate(total=Count('id')).order_by('year')

    # Converter os QuerySets em JSON
    monthly_data_json = json.dumps(list(monthly_counts))
    annual_data_json = json.dumps(list(annual_counts))

# Mapeia o número do mês para o nome do mês
    months = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    # Corrige os rótulos do gráfico
    chart_labels = []
    for entry in monthly_counts:
        month = entry.get('month')
        year = entry.get('year')
        if month and month in months:
            chart_labels.append(f"{months[month]} {year}")
        else:
            chart_labels.append(f"Mês Desconhecido {year if year else ''}")

    chart_data = {
        'labels': chart_labels,
        'data': [entry.get('total', 0) for entry in monthly_counts]
    }

    chart_data_json = json.dumps(chart_data)

    today = datetime.now().day
    expenses_due_soon = [expense for expense in fixed_expenses if 0 < (
        expense.due_day - today) <= 3]

    current_year = datetime.now().year
    last_year = current_year - 1
    current_month = datetime.now().month

    total_current = Cliente.objects.filter(
        data_de_criacao__year=current_year,
        data_de_criacao__month=current_month
    ).count()
    total_last_year = Cliente.objects.filter(
        data_de_criacao__year=last_year,
        data_de_criacao__month=current_month
    ).count()

    try:
        percent_change = (
            (total_current - total_last_year) / total_last_year) * 100
    except ZeroDivisionError:
        percent_change = 0

    vendas_corretores = VendaCorretor.objects.all().order_by('-id')

   # Calcula os top 4 status
    top_statuses_data = Cliente.objects.values('status').annotate(
        total=Count('status')).order_by('-total')[:4]

    top_statuses = [
        {
            'status': item['status'],
            'total': item['total'],
            'display': Cliente(status=item['status']).get_status_display()
        }
        for item in top_statuses_data
    ]

    clientes = Cliente.objects.all()

    processos = Processo.objects.all().order_by('-data_inicio')
    processos_em_andamento = [
        processo for processo in processos if processo.data_finalizacao is None]
    total_processos_em_andamento = len(processos_em_andamento)

    try:
        corretor_group = Group.objects.get(name='Corretores')
        corretores = corretor_group.user_set.all()
    except Group.DoesNotExist:
        corretores = []

    # Calcular o progresso para cada processo
    for processo in processos:
        processo.progresso = calcular_progresso(
            processo, processo.id, processo.cliente)

    data_referencia = datetime.now() - timedelta(days=7)
    total_clientes_recentes = Cliente.objects.filter(
        data_de_criacao__gte=data_referencia).count()

    context = {
        'total_clientes_recentes': total_clientes_recentes,
        'total_processos_em_andamento': total_processos_em_andamento,
        'current_year': current_year,
        'current_month': current_month,
        'percent_change': int(percent_change),
        'monthly_data_json': monthly_data_json,
        'annual_data_json': annual_data_json,
        'chart_data_json': chart_data_json,
        'chart_data': chart_data,
        'expenses_due_soon': expenses_due_soon,
        'total_proprietarios': total_proprietarios,
        'total_contatos': total_contatos,
        'contatos_hoje': contatos_hoje,
        'contatos_7_dias': contatos_7_dias,
        'recent_transactions': recent_transactions,
        'total_corretores': total_corretores,
        'total_clientes': total_clientes,
        'total_correspondentes': total_correspondentes,
        'saldo': saldo,
        'despesas': despesas,
        'receitas': receitas,
        'fixed_expenses': fixed_expenses,
        'dias': dias,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'notas_privadas': NotaPrivada.objects.filter(user=request.user).order_by('-data'),
        'all_statuses': all_statuses,
        'username': request.user.username,
        'vendas_corretores': vendas_corretores,
        'top_statuses': top_statuses,
        'status_choices': dict(Cliente.STATUS_CHOICES),
        'clientes': clientes,
        'processos': processos,
    }

    return render(request, 'correspondent_dashboard.html', context)


def adicionar_nota_cliente(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        texto_nota = request.POST.get('texto')

        if not texto_nota:
            return JsonResponse({'status': 'error', 'message': 'O texto da nota é obrigatório.'}, status=400)

        cliente = get_object_or_404(Cliente, pk=cliente_id)
        Nota.objects.create(cliente=cliente, texto=texto_nota)
        return JsonResponse({'status': 'success', 'message': 'Nota adicionada com sucesso.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método inválido.'}, status=405)


def carregar_notas_cliente(request, cliente_id):
    notas = Nota.objects.filter(cliente_id=cliente_id)
    notas_json = serialize('json', notas)
    return JsonResponse(notas_json, safe=False)


@require_POST
def deletar_nota_cliente(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    nota.delete()
    return JsonResponse({'status': 'success', 'message': 'Nota deletada com sucesso.'})


def lista_de_clientes(request):
    # Obtém todos os clientes inicialmente
    if is_corretor(request.user):
        # Corretor verá apenas os clientes vinculados a ele
        todos_clientes = Cliente.objects.filter(corretor=request.user)
    elif is_admin(request.user) or is_correspondent(request.user):
        # Administradores e correspondentes verão todos os clientes
        todos_clientes = Cliente.objects.all()
    else:
        # Se o usuário não for corretor, administrador ou correspondente, levante um erro 404
        raise Http404("Você não tem permissão para acessar esta página.")

    # Filtrar por status
    corretores = CustomUser.objects.filter(groups__name='Corretores')
    status_filter = request.GET.get('status')
    if status_filter:
        todos_clientes = todos_clientes.filter(status=status_filter)

    # Filtrar por corretor
    corretor_filter = request.GET.get('corretor')
    if corretor_filter:
        todos_clientes = todos_clientes.filter(corretor__pk=corretor_filter)

    # Filtrar por data

   # Filtrar por data
    data_filter = request.GET.get('data')
    if data_filter:
        try:
            data_filter = datetime.strptime(data_filter, '%Y-%m-%d')
            todos_clientes = todos_clientes.filter(
                data_de_criacao__date=data_filter)
        except ValueError:
            # Lidar com erro de formatação de data aqui, se necessário
            pass

    # Reverter a ordem para começar do último cadastrado
    todos_clientes = todos_clientes.order_by('-id')

    clientes_serializados = ClienteSerializer(todos_clientes, many=True).data

    for cliente in todos_clientes:
        cliente.notas = cliente.get_notas()
        cliente.notas_count = cliente.notas.filter(cliente=cliente).count()
        cliente.tem_nota_nova = cliente.notas.filter(nova=True).exists()

    # Obter a contagem de clientes para cada mês
    meses = []
    for i in range(1, 13):
        nome_mes = _(calendar.month_name[i])
        qtd_clientes = todos_clientes.filter(data_de_criacao__month=i).count()

        meses.append({'nome_mes': nome_mes, 'qtd_clientes': qtd_clientes})

    contexto = {
        'clientes': todos_clientes,
        'clientes_json': json.dumps(clientes_serializados),
        'username': request.user.username,
        'user_id': request.user.id,
        'meses': meses,  # Adicione a lista de meses ao contexto
        'corretor': corretores
    }

    return render(request, 'lista_clientes.html', contexto)


def deletar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    cliente.delete()
    messages.success(request, 'Cliente deletado com sucesso.')

    # Redirecione para a página 'lista_clientes'
    return redirect('lista_clientes')


def deletar_venda(request, venda_id):
    venda = get_object_or_404(VendaCorretor, id=venda_id)

    # Salva a URL referente à página atual antes da deleção
    referer_url = request.META.get('HTTP_REFERER', None)

    if request.method == 'POST':
        venda.delete()
        messages.success(request, 'Venda deletada com sucesso.')

        # Redireciona para a URL salva (página anterior)
        return redirect(referer_url)

    # Não precisa mais renderizar o template
    return HttpResponse(status=204)


def atualizar_status_cliente(request):
    try:
        if request.method == 'POST':
            cliente_id = request.POST.get('cliente_id')
            novo_status = request.POST.get('novo_status')

            # Atualizar o status do cliente
            cliente = Cliente.objects.get(pk=cliente_id)
            cliente.status = novo_status
            cliente.save()

            # Chame a função send_notification aqui
            send_notification(cliente)

            # Enviar uma resposta indicando sucesso
            return JsonResponse({"status": "success"})
    except Exception as e:
        # Isso retornará a descrição do erro para a resposta, ajudando na depuração.
        return JsonResponse({"status": "error", "error_message": str(e)})

    # Se algo der errado, retorne uma resposta de erro
    return JsonResponse({"status": "error", "error_message": "Método inválido ou outra falha"})


def lista_de_corretores(request):
    if request.method == 'POST':
        try:
            corretor_id = request.POST.get('corretor_id')
            corretor_email = request.POST.get('email')
            corretor_senha = request.POST.get('senha')

            corretor = get_object_or_404(Corretores, id=corretor_id)
            corretor.email = corretor_email
            if corretor_senha:
                corretor.set_password(corretor_senha)
            corretor.save()

            return JsonResponse({'success': True})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)})

    todos_corretores = Corretores.objects.all()
    return render(request, 'lista_corretores.html', {'corretores': todos_corretores})


def atualizar_corretor(request, corretor_id):
    if request.method == 'POST':
        corretor = get_object_or_404(Corretores, id=corretor_id)
        corretor.email = request.POST.get('email')

        senha = request.POST.get('senha')
        if senha:
            corretor.set_password(senha)

        corretor.save()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Método inválido'}, status=400)


@login_required
def cadastro_corretores(request):
    if request.method == 'POST':
        form = CorretorForm(request.POST)
        if form.is_valid():
            # Primeiro, salve o objeto Corretor sem fazer commit no banco
            corretor = form.save(commit=False)

            # Adicione o prefixo +55 ao telefone
            telefone = form.cleaned_data.get('telefone')
            if telefone and not telefone.startswith('55'):
                corretor.telefone = '55' + telefone

            # Defina a senha usando set_password
            corretor.set_password(form.cleaned_data['password'])

            corretor.save()
            return HttpResponseRedirect(reverse('admin_dashboard'))
    else:
        form = CorretorForm()
    return render(request, 'cadastro_corretores.html', {'form': form, 'username': request.user.username})

# cadastro de clientes


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            cliente = form.save()
            folder_path = os.path.join(
                "media/documentos", f"{cliente.nome}-{cliente.cpf}")
            os.makedirs(folder_path, exist_ok=True)

            uploaded_files = request.FILES.getlist('documentos')
            pdf_writer = fitz.open()  # Cria um novo documento PDF

            for uploaded_file in uploaded_files:
                file_path = os.path.join(folder_path, uploaded_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                ext = os.path.splitext(uploaded_file.name)[1].lower()
                try:
                    if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                        img = Image.open(file_path)
                        img_pdf_path = file_path + '.pdf'
                        img.save(img_pdf_path, "PDF", resolution=100.0)
                        pdf_writer.insert_pdf(fitz.open(img_pdf_path))
                    elif ext in ['.pdf']:
                        pdf_writer.insert_pdf(fitz.open(file_path))
                except Exception as e:
                    error_message = f"Erro ao processar o arquivo {uploaded_file.name}: {e}"
                    messages.error(request, error_message)
                    print(error_message)

            final_pdf_path = os.path.join(
                folder_path, f"{cliente.nome}-{cliente.cpf}_documentos.pdf")
            try:
                pdf_writer.save(final_pdf_path)
                send_notification_to_correspondente(cliente)
            except Exception as e:
                error_message = f"Erro ao salvar o PDF final: {e}"
                messages.error(request, error_message)
                print(error_message)
                # send_notification_to_correspondente(cliente)
            finally:
                pdf_writer.close()

    else:
        form = ClienteForm()

    corretores = Corretores.objects.all()

    return render(request, 'cliente_form_template.html', {'form': form, 'username': request.user.username, 'corretores': corretores})


@csrf_exempt
def atualizar_cliente(request, client_id):
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(pk=client_id)
        except Cliente.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cliente não encontrado.'}, status=404)

        # Processar os dados do cliente
        novo_status = request.POST.get('novo_status')
        nota_texto = request.POST.get('nota')

        if novo_status:
            cliente.status = novo_status
            cliente.save()

        if nota_texto:
            Nota.objects.create(cliente=cliente, texto=nota_texto)

        documentos = request.FILES.getlist('documentos')
        if documentos:
            folder_path = os.path.join(
                "media/documentos", f"{cliente.nome}-{cliente.cpf}")
            os.makedirs(folder_path, exist_ok=True)
            pdf_filename = os.path.join(
                folder_path, f"{cliente.nome}-{cliente.cpf}.pdf")

            pdf_writer = PdfWriter()

            if os.path.exists(pdf_filename) and os.path.getsize(pdf_filename) > 0:
                with open(pdf_filename, "rb") as existing_pdf_file:
                    existing_pdf = PdfReader(existing_pdf_file)
                    for page in existing_pdf.pages:
                        pdf_writer.add_page(page)

            for uploaded_file in documentos:
                new_path = os.path.join(
                    folder_path, os.path.basename(uploaded_file.name))
                with open(new_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                try:
                    if uploaded_file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
                        with Image.open(new_path) as img:
                            img.convert('RGB').save(new_path, format='PDF')
                            with open(new_path, "rb") as img_pdf_file:
                                pdf_writer.add_page(
                                    PdfReader(img_pdf_file).pages[0])
                    elif uploaded_file.name.lower().endswith('.pdf'):
                        with open(new_path, "rb") as new_pdf_file:
                            new_pdf = PdfReader(new_pdf_file)
                            for page in new_pdf.pages:
                                pdf_writer.add_page(page)
                finally:
                    os.remove(new_path)

            with open(pdf_filename, "wb") as out_pdf_file:
                pdf_writer.write(out_pdf_file)

        return JsonResponse({'status': 'success', 'message': 'Cliente atualizado com sucesso.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método inválido.'}, status=405)


@login_required
def cadastro_correspondentes(request):
    if request.method == 'POST':
        form = CorrespondenteForm(request.POST)
        if form.is_valid():
            correspondente = form.save(commit=False)  # Não salve ainda

            # Adicione o prefixo +55 ao telefone
            telefone = form.cleaned_data.get('telefone')
            if telefone and not telefone.startswith('55'):
                correspondente.telefone = '55' + telefone

            correspondente.set_password(form.cleaned_data['password'])
            correspondente.save()

            # Tente obter o grupo "correspondente" ou crie se não existir
            group, _ = Group.objects.get_or_create(name='correspondente')

            # Adicione o correspondente ao grupo
            # Verifique se 'correspondente' é uma instância do modelo User
            if isinstance(correspondente, User):
                group.user_set.add(correspondente)

            return HttpResponseRedirect(reverse('admin_dashboard'))

    else:
        form = CorrespondenteForm()

    return render(request, 'cadastro_correspondentes.html', {'form': form, 'username': request.user.username})


@csrf_exempt
@login_required
def consulta_cpf(request):
    if request.method == "POST":
        cpf_raw = request.POST.get('cpf', '')
        cpf = re.sub(r'[^0-9]', '', cpf_raw)

        if not cpf or len(cpf) != 11:
            return JsonResponse({'error': 'CPF inválido'})

        result = consulta_cpf_func(cpf)
        return JsonResponse(result)

    return render(request, 'consulta_cpf.html', {'username': request.user.username})


@user_passes_test(is_admin)
@login_required
def admin_dashboard(request):
    # Coleta de dados
    fixed_expenses = get_fixed_expenses(request.user)
    dias = [i for i in range(1, 32)]

    despesas = Transaction.objects.filter(tipo='DESPESA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    receitas = Transaction.objects.filter(tipo='RECEITA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    total_receitas = Transaction.objects.filter(
        user=request.user, tipo='RECEITA').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas = Transaction.objects.filter(
        user=request.user, tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    saldo = receitas - despesas

    # Obter a contagem de vários modelos
    total_corretores = Corretores.objects.count()
    total_clientes = Cliente.objects.count()
    total_correspondentes = Correspondente.objects.count()
    recent_transactions = Transaction.objects.all().order_by('-id')[:8]

    total_proprietarios = Proprietario.objects.count()
    total_contatos = Contato.objects.count()
    contatos_hoje = Contato.objects.filter(
        data_registro=datetime.now().date()).count()
    contatos_7_dias = Contato.objects.filter(
        data_registro__gte=datetime.now() - timedelta(days=7)).count()

    status_counts = Cliente.objects.values(
        'status').annotate(total=Count('status'))
    status_counts_dict = {item['status']: item['total']
                          for item in status_counts}
    all_statuses = [
        {'status': choice[0], 'total': status_counts_dict.get(
            choice[0], 0), 'display': choice[1]}
        for choice in Cliente.STATUS_CHOICES
    ]

    # Converta STATUS_CHOICES em um dicionário para fácil acesso
    status_dict = dict(Cliente.STATUS_CHOICES)

    # Gerar dados mensais
    monthly_counts = Cliente.objects.filter(data_de_criacao__isnull=False).annotate(
        month=ExtractMonth('data_de_criacao'),
        year=ExtractYear('data_de_criacao')
    ).values('month', 'year').annotate(total=Count('id')).order_by('year', 'month')

    # Gerar dados anuais
    annual_counts = Cliente.objects.filter(data_de_criacao__isnull=False).annotate(
        year=ExtractYear('data_de_criacao')
    ).values('year').annotate(total=Count('id')).order_by('year')

    # Converter os QuerySets em JSON
    monthly_data_json = json.dumps(list(monthly_counts))
    annual_data_json = json.dumps(list(annual_counts))

# Mapeia o número do mês para o nome do mês
    months = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    # Corrige os rótulos do gráfico
    chart_labels = []
    for entry in monthly_counts:
        month = entry.get('month')
        year = entry.get('year')
        if month and month in months:
            chart_labels.append(f"{months[month]} {year}")
        else:
            chart_labels.append(f"Mês Desconhecido {year if year else ''}")

    chart_data = {
        'labels': chart_labels,
        'data': [entry.get('total', 0) for entry in monthly_counts]
    }

    chart_data_json = json.dumps(chart_data)

    today = datetime.now().day
    expenses_due_soon = [expense for expense in fixed_expenses if 0 < (
        expense.due_day - today) <= 3]

    current_year = datetime.now().year
    last_year = current_year - 1
    current_month = datetime.now().month

    total_current = Cliente.objects.filter(
        data_de_criacao__year=current_year,
        data_de_criacao__month=current_month
    ).count()
    total_last_year = Cliente.objects.filter(
        data_de_criacao__year=last_year,
        data_de_criacao__month=current_month
    ).count()

    try:
        percent_change = (
            (total_current - total_last_year) / total_last_year) * 100
    except ZeroDivisionError:
        percent_change = 0

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        print("POST recebido")

        if form_type == 'transacao':
            print("Transação recebida")
            description = request.POST.get('description')
            tipo = request.POST.get('tipo')
            valor = request.POST.get('valor')

            if not (description and tipo and valor):
                messages.error(request, "Por favor, preencha todos os campos.")
                return redirect('admin_dashboard')

            if tipo == "DESPESA_FIXA":
                due_day = request.POST.get('due_day') or 1
                FixedExpense.objects.create(description=description, due_day=int(
                    due_day), amount=valor, user=request.user)
                messages.success(
                    request, "Despesa fixa adicionada com sucesso.")
            else:
                Transaction.objects.create(
                    description=description, tipo=tipo, valor=valor, user=request.user)
                messages.success(request, "Transação adicionada com sucesso.")

        elif form_type == 'vendas_corretor':
            print("Registro recebido")
            nome = request.POST.get('nome')
            valor_total_pagar = request.POST.get('valor_total_pagar')
            valor_pago = request.POST.get('valor_pago')
            nome_corretor = request.POST.get('nome_corretor')
            valor_faltante = request.POST.get('valor_faltante')
            tipo = request.POST.get('tipo')

            try:
                VendaCorretor.objects.create(
                    nome=nome,
                    valor_total_pagar=float(valor_total_pagar),
                    valor_pago=float(valor_pago),
                    nome_corretor=nome_corretor,
                    valor_faltante=float(valor_faltante),
                    tipo=tipo
                )
                messages.success(
                    request, "Venda por corretor adicionada com sucesso.")
            except Exception as e:
                messages.error(request, f"Erro ao adicionar venda: {e}")

        return redirect('admin_dashboard')

    vendas_corretores_list = VendaCorretor.objects.all()
    paginator = Paginator(vendas_corretores_list, 5)

    page_number = request.GET.get('page')
    vendas_corretores = paginator.get_page(page_number)
    clientes = Cliente.objects.all()
    corretores = Corretores.objects.all()

    context = {
        'corretores': corretores,
        'current_year': current_year,
        'current_month': current_month,
        'percent_change': int(percent_change),
        'monthly_data_json': monthly_data_json,
        'annual_data_json': annual_data_json,
        'chart_data_json': chart_data_json,
        'chart_data': chart_data,
        'expenses_due_soon': expenses_due_soon,
        'total_proprietarios': total_proprietarios,
        'total_contatos': total_contatos,
        'contatos_hoje': contatos_hoje,
        'contatos_7_dias': contatos_7_dias,
        'recent_transactions': recent_transactions,
        'total_corretores': total_corretores,
        'total_clientes': total_clientes,
        'total_correspondentes': total_correspondentes,
        'saldo': saldo,
        'despesas': despesas,
        'receitas': receitas,
        'fixed_expenses': fixed_expenses,
        'dias': dias,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'notas_privadas': NotaPrivada.objects.filter(user=request.user).order_by('-data'),
        'all_statuses': all_statuses,
        'username': request.user.username,
        'vendas_corretores': vendas_corretores,
        'clientes': clientes
    }

    return render(request, 'admin_dashboard.html', context)


def delete_expense(request, expense_id):
    if expense_id:  # Verifica se o ID não está vazio
        expense = get_object_or_404(FixedExpense, id=expense_id)
        expense.delete()

    return redirect('admin_dashboard')


# Financeiro

class DecimalEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def calcular_saldo(data):
    saldo = 0
    for item in data:
        receitas = item.get('receitas', Decimal('0')) or Decimal('0')
        despesas = item.get('despesas', Decimal('0')) or Decimal('0')

        item['saldo'] = receitas - despesas
        saldo += item['saldo']
        item['saldo_total'] = saldo

    return data

# Sua view completa


def financas_view(request):

    transacoes = Transaction.objects.filter(
        user=request.user).order_by('id')  # Adicione 'order_by' aqui

    if request.method == 'POST':

        form = TransactionForm(request.POST)

        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.user = request.user
            transacao.save()
            print(form)

            return redirect('financas_view')
    else:
        form = TransactionForm()

    totais_mensais = transacoes.annotate(
        mes=ExtractMonth('created_at'),
        ano=ExtractYear('created_at')
    ).values('mes', 'ano').annotate(
        receitas=Sum('valor', filter=Q(tipo='receita')),
        despesas=Sum('valor', filter=Q(tipo='despesa'))
    ).order_by('ano', 'mes')

    totais_anuais = transacoes.annotate(
        ano=ExtractYear('created_at')
    ).values('ano').annotate(
        receitas=Sum('valor', filter=Q(tipo='receita')),
        despesas=Sum('valor', filter=Q(tipo='despesa'))
    ).order_by('ano')

    totais_mensais_saldo = calcular_saldo(list(totais_mensais))
    totais_anuais_saldo = calcular_saldo(list(totais_anuais))

    totais_mensais_json = json.dumps(
        list(totais_mensais_saldo), cls=DecimalEncoder)
    totais_anuais_json = json.dumps(
        list(totais_anuais_saldo), cls=DecimalEncoder)
    totais_mensais_json_saldo = json.dumps(
        list(totais_mensais_saldo), cls=DecimalEncoder)
    totais_anuais_json_saldo = json.dumps(
        list(totais_anuais_saldo), cls=DecimalEncoder)

    monthly_data_json = json.dumps(
        [{'month': item['mes'], 'year': item['ano'], 'total': (item['receitas'] or Decimal('0')) - (item['despesas'] or Decimal('0'))} for item in totais_mensais_saldo], cls=DecimalEncoder
    )

    annual_data_json = json.dumps(
        [{'year': item['ano'], 'total': (item['receitas'] or Decimal('0')) - (item['despesas'] or Decimal('0'))} for item in totais_anuais_saldo], cls=DecimalEncoder
    )

    # Aplicar filtro com base na descrição, se fornecido
    search_description = request.GET.get('search_description')
    if search_description:
        transacoes = transacoes.filter(
            description__icontains=search_description)

    # Configuração da paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(transacoes, 5)

    try:
        transacoes = paginator.page(page)
    except PageNotAnInteger:
        transacoes = paginator.page(1)
    except EmptyPage:
        transacoes = paginator.page(paginator.num_pages)

    # Cálculo do total geral de receitas e despesas
    total_receita_geral = totais_mensais.aggregate(Sum('receitas'))[
        'receitas__sum'] or 0
    total_despesa_geral = totais_mensais.aggregate(Sum('despesas'))[
        'despesas__sum'] or 0
    total_geral = total_receita_geral - total_despesa_geral

    return render(request, 'financas.html', {
        'transacoes': transacoes,
        'form': form,
        'totais_mensais_json': totais_mensais_json,
        'totais_anuais_json': totais_anuais_json,
        'totais_mensais_json_saldo': totais_mensais_json_saldo,
        'totais_anuais_json_saldo': totais_anuais_json_saldo,
        'monthly_data_json': monthly_data_json,
        'annual_data_json': annual_data_json,
        'total_receita_geral': total_receita_geral,
        'total_despesa_geral': total_despesa_geral,
        'total_geral': total_geral,
        'username': request.user.username,
    })


# Adicione esta nova view para lidar com a solicitação AJAX


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.delete()
    return redirect('financas_view')


def filtrar_por_mes_ano(request):
    if request.method == 'GET':
        user = request.user
        mes = request.GET.get('mes')
        ano = request.GET.get('ano')

        # Filtre as transações com base no mês e no ano
        transacoes_filtradas = Transaction.objects.filter(
            user=user,
            created_at__month=mes,
            created_at__year=ano
        )

        # Realize as operações necessárias para obter os totais mensais e anuais
        totais_mensais = transacoes_filtradas.annotate(
            mes=ExtractMonth('created_at'),
            ano=ExtractYear('created_at')
        ).values('mes', 'ano').annotate(
            receitas=Sum('valor', filter=Q(tipo='receita')),
            despesas=Sum('valor', filter=Q(tipo='despesa'))
        ).order_by('ano', 'mes')

        totais_anuais = transacoes_filtradas.annotate(
            ano=ExtractYear('created_at')
        ).values('ano').annotate(
            receitas=Sum('valor', filter=Q(tipo='receita')),
            despesas=Sum('valor', filter=Q(tipo='despesa'))
        ).order_by('ano')

        totais_mensais_saldo = calcular_saldo(list(totais_mensais))
        totais_anuais_saldo = calcular_saldo(list(totais_anuais))

        # Retorne os totais mensais e anuais como JSON
        data = {
            'totais_mensais': totais_mensais_saldo,
            'totais_anuais': totais_anuais_saldo,
        }
        return JsonResponse(data, safe=False)


def get_fixed_expenses(user):
    today = datetime.today()
    for expense in FixedExpense.objects.filter(user=user):
        if expense.month_paid and expense.month_paid != today.month:
            expense.is_paid = False
            expense.save()
    return FixedExpense.objects.filter(user=user)


def calcular_porcentagem(valor_atual, valor_anterior):
    if valor_anterior == 0:
        return 0
    return ((valor_atual - valor_anterior) / valor_anterior) * 100


@login_required
def lista_proprietarios(request):
    # Pega os objetos do banco de dados
    proprietarios = Proprietario.objects.all()
    notas_privadas = NotaPrivada.objects.filter(
        user=request.user).order_by('-data')

    # Pega os contadores para Proprietarios e Contatos
    total_proprietarios = proprietarios.count()
    total_contatos = Contato.objects.count()
    contatos_hoje = Contato.objects.filter(
        data_registro=timezone.now().date()).count()
    contatos_7_dias = Contato.objects.filter(
        data_registro__gte=timezone.now() - timezone.timedelta(days=7)).count()

    # Substitua os valores abaixo pelas chamadas de banco de dados apropriadas ou outra lógica
    total_proprietarios_last_month = 100
    total_contatos_last_week = 150
    contatos_hoje_yesterday = 10
    contatos_14_7_dias = 50

    # Calcular porcentagens
    proprietarios_percentage = calcular_porcentagem(
        total_proprietarios, total_proprietarios_last_month)
    contatos_percentage = calcular_porcentagem(
        total_contatos, total_contatos_last_week)
    contatos_hoje_percentage = calcular_porcentagem(
        contatos_hoje, contatos_hoje_yesterday)
    contatos_7_dias_percentage = calcular_porcentagem(
        contatos_7_dias, contatos_14_7_dias)

    # Configuração de paginação para notas
    paginator = Paginator(notas_privadas, 5)  # Mostrar 10 notas por página
    page_number = request.GET.get('page')
    notas_paginadas = paginator.get_page(page_number)

    context = {
        'proprietarios': proprietarios,
        'notas_privadas': notas_paginadas,
        'form': ProprietarioForm(),
        'total_proprietarios': total_proprietarios,
        'total_contatos': total_contatos,
        'contatos_hoje': contatos_hoje,
        'contatos_7_dias': contatos_7_dias,
        'proprietarios_percentage': proprietarios_percentage,
        'contatos_percentage': contatos_percentage,
        'contatos_hoje_percentage': contatos_hoje_percentage,
        'contatos_7_dias_percentage': contatos_7_dias_percentage,
        'username': request.user.username
    }
    return render(request, 'lista_proprietarios.html', context)


def adicionar_nota(request):
    if request.method == "POST":
        conteudo = request.POST.get('conteudo')
        nota = NotaPrivada(user=request.user, conteudo=conteudo)
        nota.save()
        return redirect('lista_proprietarios')


def editar_nota(request, nota_id):
    nota = get_object_or_404(NotaPrivada, id=nota_id)

    if request.method == "POST":
        conteudo = request.POST.get('conteudo')
        nota.conteudo = conteudo
        nota.save()
        return redirect('lista_proprietarios')
    else:
        context = {
            'nota': nota
        }
        return render(request, 'lista_proprietarios.html', context)


def concluir_nota(request, nota_id):
    nota = get_object_or_404(NotaPrivada, id=nota_id)
    nota.concluido = True
    nota.save()
    return redirect('lista_proprietarios')


def deletar_nota(request, nota_id):
    nota = get_object_or_404(NotaPrivada, id=nota_id)
    nota.delete()
    return redirect('lista_proprietarios')


@login_required
def add_fixed_expense(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        due_day = int(request.POST.get('due_day'))
        amount = request.POST.get('amount')
        user = request.user

        # Cria uma nova despesa fixa e salva no banco de dados
        FixedExpense.objects.create(
            description=description, due_day=due_day, amount=amount, user=user)

        # Redireciona para a página do dashboard após adicionar a despesa
        return redirect('admin_dashboard')

    dias = list(range(1, 32))
    context = {
        'dias': dias
    }
    return render(request, 'admin_dashboard.html', context)


def reset_fixed_expenses():
    last_month = datetime.today().month - 1
    if last_month == 0:
        last_month = 12
    FixedExpense.objects.filter(month_paid=last_month).update(
        is_paid=False, month_paid=None)


@login_required
def mark_as_paid(request, expense_id):
    expense = get_object_or_404(FixedExpense, id=expense_id, user=request.user)
    expense.is_paid = True
    expense.month_paid = date.today().month
    expense.save()
    return redirect('admin_dashboard')


def toggle_expense_status(request, expense_id):
    expense = FixedExpense.objects.get(id=expense_id)
    expense.is_paid = not expense.is_paid
    expense.save()
    return redirect('admin_dashboard')


def delete_expense(request, expense_id):
    expense = get_object_or_404(FixedExpense, id=expense_id)
    expense.delete()
    messages.success(request, "Despesa excluída com sucesso.")
    return redirect('admin_dashboard')


# Função whatsapp notificação


@csrf_exempt
def send_notification(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        clienteId = data.get('cliente_id')

        try:
            cliente = Cliente.objects.get(pk=clienteId)

            whatsapp_num = f"{cliente.corretor.telefone}@c.us"
            message = f'O status do cliente *{cliente.nome}*  foi atualizado para *{cliente.status.replace("_", " ")}*.'

            payload = {
                'number': whatsapp_num,
                'message': message
            }

            response = requests.post(
                'http://localhost:3000/send-message', json=payload)

            if response.json().get('success'):
                return JsonResponse({"message": "Notification sent successfully"})
            else:
                error_message = response.json().get('error', 'Unknown error')
                return JsonResponse({"error": f"Failed to send the message on WhatsApp due to: {error_message}"}, status=500)
        except Cliente.DoesNotExist:
            return JsonResponse({"error": "Cliente not found"}, status=404)


def send_notification_to_correspondente(cliente):
    correspondentes = Correspondente.objects.all()
    success = 0
    failed = 0

    message = f'O cliente *{cliente.nome}* foi cadastrado com sucesso no sistema. Por favor, verifique o CRM :)'

    for correspondente in correspondentes:
        try:
            # formatando o telefone
            whatsapp_num = f"{correspondente.telefone}@c.us"

            payload = {
                'number': whatsapp_num,
                'message': message
            }

            response = requests.post(
                'http://localhost:3000/send-message', json=payload)

            if response.json().get('success'):
                success += 1
            else:
                error_message = response.json().get('error', 'Unknown error')
                print(
                    f"Failed to send the message to {whatsapp_num} due to: {error_message}")
                failed += 1

        except Exception as e:
            print(f"Error sending to {whatsapp_num}: {str(e)}")
            failed += 1

    return {"message": f"Notifications sent successfully to {success} correspondentes, failed for {failed}."}


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_correspondente)
def lista_de_corretores(request):
    corretores = Corretores.objects.all()

    if request.method == 'POST':
        form = CorretorForm(request.POST)
        if form.is_valid():
            form.save()
            # Retorne uma mensagem de sucesso se desejar

    return render(request, 'listadecorretores.html', {'corretores': corretores, 'username': request.user.username})


@login_required
def settings_view(request):
    # Inicialização padrão dos forms
    form = UserSettingsForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_settings' in request.POST:
            form = UserSettingsForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 'Configurações atualizadas com sucesso!')
                return redirect('settings')
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Atualiza a sessão após a mudança de senha para evitar deslogar o usuário
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('settings')
            else:
                messages.error(request, 'Erro ao alterar a senha.')

    context = {
        'form': form,
        'password_form': password_form,
        'username': request.user.username
    }

    return render(request, 'settings_template.html', context)


@login_required
def adicionar_proprietario(request):
    if request.method == 'POST':
        form = ProprietarioForm(request.POST)
        if form.is_valid():
            form.save()
            # Suponho que 'lista_proprietarios' seja a URL da sua lista
            return redirect('lista_proprietarios')
    else:
        form = ProprietarioForm()
    return render(request, 'lista_proprietarios.html', {'form': form})


def calcular_progresso(processo, processo_id, cliente):
    processo = get_object_or_404(Processo, id=processo_id, cliente=cliente)

    tipo_processo = TipoProcesso.objects.get(nome=processo.tipo)
    opcoes_disponiveis = [opcao.strip()
                          for opcao in tipo_processo.obter_opcoes()]
    opcoes_selecionadas = OpcaoSelecionada.objects.filter(processo=processo)

    if not opcoes_disponiveis:
        return 0

    progresso = len(opcoes_selecionadas) / len(opcoes_disponiveis) * 100
    return int(progresso)


@login_required
def lista_processos(request):
    processos = Processo.objects.all()
    total_processos = processos.count()  # Count total processes

    clientes = Cliente.objects.all()
    total_contatos = clientes.count()  # Count total contacts

    proprietarios = Proprietario.objects.all()

    corretor_group = get_object_or_404(Group, name='Corretores')
    corretores = corretor_group.user_set.all()

    # Calcular o progresso para cada processo
    for processo in processos:
        processo.progresso = int(calcular_progresso(
            processo, processo.id, processo.cliente))

    return render(request, 'processos.html', {
        'processos': processos,
        'total_processos': total_processos,
        'clientes': clientes,
        'total_contatos': total_contatos,
        'corretores': corretores,
        'username': request.user.username,
        'proprietarios': proprietarios,
    })


@login_required
def add_processo(request):
    clientes = Cliente.objects.all()
    tipos_processo = TipoProcesso.objects.all()
    proprietarios = Proprietario.objects.all()

    if request.method == "POST":
        cliente_id = request.POST.get('cliente')
        cliente_instance = Cliente.objects.get(id=cliente_id)

        # Altere o nome do campo para 'tipo'
        tipo_nome = request.POST.get('tipo')
        tags = request.POST.get('tags')
        responsavel_id = request.POST.get('responsavel')

        # Obtendo o objeto Corretores com base no ID
        responsavel_instance = Corretores.objects.get(id=responsavel_id)

        data_inicio_str = request.POST.get('data_inicio')
        data_finalizacao_str = request.POST.get('data_finalizacao')

        # Convertendo strings para objetos de data
        data_inicio = datetime.strptime(
            data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else None
        data_finalizacao = datetime.strptime(
            data_finalizacao_str, '%Y-%m-%d').date() if data_finalizacao_str else None

        # Verificar se o tipo de processo já existe
        tipo_processo, created = TipoProcesso.objects.get_or_create(
            nome=tipo_nome)

        # Adicione a obtenção do proprietário
        proprietario_id = request.POST.get('proprietario')
        proprietario_instance = Proprietario.objects.get(id=proprietario_id)

        # Crie o processo incluindo o proprietário
        Processo.objects.create(
            cliente=cliente_instance,
            tipo=tipo_processo,
            tags=tags,
            responsavel=responsavel_instance,
            data_inicio=data_inicio,
            data_finalizacao=data_finalizacao,
            proprietario=proprietario_instance  # Adicione o proprietário aqui
        )

        return redirect('lista_processos')

    return render(request, 'processo.html', {'clientes': clientes, 'tipos_processo': tipos_processo, 'proprietarios': proprietarios})


# views.py

@login_required
def cliente_processo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    processos = Processo.objects.filter(cliente=cliente)

    return render(
        request,
        'cliente_processo.html',
        {
            'cliente': cliente,
            'processos': processos,
            'username': request.user.username
        }
    )


@login_required
def detalhes_do_processo(request, cliente_id, processo_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    processo = get_object_or_404(Processo, id=processo_id, cliente=cliente)

    tipo_processo = TipoProcesso.objects.get(nome=processo.tipo)
    opcoes_disponiveis = [opcao.strip()
                          for opcao in tipo_processo.obter_opcoes()]
    opcoes_selecionadas = OpcaoSelecionada.objects.filter(processo=processo)

    opcoes_selecionadas_list = [opcao.opcao.strip()
                                for opcao in opcoes_selecionadas]

    if request.method == "POST":
        form = OpcoesForm(request.POST, tipos_processo=[
                          tipo_processo], opcoes_selecionadas=opcoes_selecionadas)
        if form.is_valid():
            OpcaoSelecionada.objects.filter(
                cliente=cliente, processo=processo, tipo_processo=tipo_processo).delete()

            for opcao in form.cleaned_data['opcoes_processo']:
                OpcaoSelecionada.objects.create(
                    cliente=cliente, processo=processo, tipo_processo=tipo_processo, opcao=opcao)

            opcoes_selecionadas = OpcaoSelecionada.objects.filter(
                processo=processo)
            opcoes_selecionadas_list = [
                opcao.opcao.strip() for opcao in opcoes_selecionadas]

            form = OpcoesForm(
                tipos_processo=[tipo_processo], opcoes_selecionadas=opcoes_selecionadas)
    else:
        form = OpcoesForm(
            tipos_processo=[tipo_processo], opcoes_selecionadas=opcoes_selecionadas)

    return render(request, 'cliente_processo.html', {
        'cliente': cliente,
        'processo': processo,
        'tipo_processo': tipo_processo,
        'form': form,
        'opcoes_selecionadas': opcoes_selecionadas,
        'opcoes_selecionadas_list': opcoes_selecionadas_list,
        'opcoes_disponiveis': opcoes_disponiveis,
        'username': request.user.username
    })
