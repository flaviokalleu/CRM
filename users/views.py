import requests
from .models import Cliente, Corretor
import shutil
from PyPDF2 import DocumentInformation
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
from .models import Cliente, Corretor, Correspondente, Transaction, FixedExpense, Documento
from django.db import models
from datetime import datetime
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import fitz
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


from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
import requests
# Importando o modelo UserAccessLog que você deve ter definido anteriormente
from .models import UserAccessLog


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

    corretor_instance = Corretor.objects.get(pk=request.user.pk)
    clientes = Cliente.objects.filter(corretor=corretor_instance)

    contexto = {
        'clientes': clientes,
        'top_statuses': top_statuses,
        'status_choices': dict(Cliente.STATUS_CHOICES),
    }

    return render(request, 'broker_dashboard.html', contexto)


@user_passes_test(is_correspondent)
@login_required
def correspondent_dashboard(request):
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

    contexto = {
        'clientes': clientes,
        'top_statuses': top_statuses,
        'status_choices': dict(Cliente.STATUS_CHOICES),
    }
    return render(request, 'correspondent_dashboard.html', contexto)


def lista_de_clientes(request):
    todos_clientes = Cliente.objects.select_related('corretor').all()
    clientes_serialized = serialize('json', todos_clientes)

    contexto = {
        'clientes': todos_clientes,
        'clientes_json': clientes_serialized
    }
    return render(request, 'lista_clientes.html', contexto)


def atualizar_status_cliente(request):
    try:
        if request.method == 'POST':
            cliente_id = request.POST.get('cliente_id')
            novo_status = request.POST.get('novo_status')

            # Atualizar o status do cliente
            cliente = Cliente.objects.get(pk=cliente_id)
            cliente.status = novo_status
            cliente.save()

            # Enviar uma resposta indicando sucesso
            return JsonResponse({"status": "success"})
    except Exception as e:
        # Isso retornará a descrição do erro para a resposta, ajudando na depuração.
        return JsonResponse({"status": "error", "error_message": str(e)})

    # Se algo der errado, retorne uma resposta de erro
    return JsonResponse({"status": "error", "error_message": "Método inválido ou outra falha"})


def lista_de_corretores(request):
    # Buscar todos os corretores do banco de dados.
    todos_corretores = Corretor.objects.all()

    contexto = {
        'corretores': todos_corretores,
    }
    return render(request, 'lista_corretores.html', contexto)


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
    return render(request, 'cadastro_corretores.html', {'form': form})


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                cliente = form.save()

                # Criando a pasta para os documentos do cliente
                folder_path = os.path.join(
                    "media/documentos", f"{cliente.nome}-{cliente.cpf}")
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)

                # Salvando os documentos
                uploaded_files = request.FILES.getlist('documentos')
                images = []
                saved_files = []  # Lista para armazenar caminhos dos arquivos salvos

                for uploaded_file in uploaded_files:
                    doc = Documento.objects.create(
                        cliente=cliente, arquivo=uploaded_file)

                    # Movendo o arquivo para a pasta do cliente
                    new_path = os.path.join(
                        folder_path, os.path.basename(doc.arquivo.path))
                    shutil.move(doc.arquivo.path, new_path)
                    saved_files.append(new_path)

                    # Verificando se o arquivo é uma imagem. Se for, a adicionamos à lista de imagens.
                    ext = os.path.splitext(uploaded_file.name)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.pdf']:
                        img = Image.open(new_path)
                        images.append(img.convert('RGB'))

                # Criando um único PDF
                if images:
                    pdf_filename = os.path.join(
                        folder_path, f"{cliente.nome}-{cliente.cpf}.pdf")
                    images[0].save(pdf_filename, save_all=True,
                                   append_images=images[1:])

                    # Removendo arquivos originais, deixando apenas o PDF
                    for file_path in saved_files:
                        os.remove(file_path)

                messages.success(
                    request, "Cliente foi cadastrado com sucesso!")

            except ValidationError as e:
                for message in e.messages:
                    messages.error(request, message)

            except Exception as e:
                messages.error(
                    request, f"Ocorreu um erro inesperado: {str(e)}")

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = ClienteForm()

    return render(request, 'cliente_form_template.html', {'form': form})


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

    return render(request, 'cadastro_correspondentes.html', {'form': form})


@login_required
def finance_dashboard(request):
    transactions = Transaction.objects.all()
    balance = sum([t.valor for t in transactions if t.tipo == "RECEITA"]) - \
        sum([t.valor for t in transactions if t.tipo == "DESPESA"])

    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance_dashboard')
    else:
        form = TransactionForm()

    context = {
        'transactions': transactions,
        'balance': balance,
        'form': form
    }
    return render(request, 'finance_dashboard.html', context)


@csrf_exempt
def consulta_cpf(request):
    if request.method == "POST":
        cpf = request.POST['cpf']
        cpf = re.sub(r'[^0-9]', '', cpf)

        result = consulta_cpf_func(cpf)
        return JsonResponse(result)

    return render(request, 'consulta_cpf.html')


@login_required
@user_passes_test(is_admin)
@login_required
def admin_dashboard(request):
    # Pegando todas as despesas fixas
    fixed_expenses = FixedExpense.objects.all()

    # Gerando uma lista com os dias do mês
    dias = [i for i in range(1, 32)]

    if request.method == 'POST':
        description = request.POST.get('description')
        tipo = request.POST.get('tipo')
        valor = request.POST.get('valor')
        user = request.user

        if not (description and tipo and valor):
            messages.error(request, "Por favor, preencha todos os campos.")
            return redirect('admin_dashboard')

        if tipo == "DESPESA_FIXA":
            due_day = request.POST.get('due_day')
            if not due_day:
                due_day = 1  # Valor padrão, você pode ajustar conforme necessário
            else:
                due_day = int(due_day)

            # Cria uma nova despesa fixa
            FixedExpense.objects.create(
                description=description, due_day=due_day, amount=valor, user=user)

            messages.success(request, "Despesa fixa adicionada com sucesso.")
        else:
            # Cria uma nova transação (DESPESA ou RECEITA)
            Transaction.objects.create(
                description=description, tipo=tipo, valor=valor, user=user)

            messages.success(request, "Transação adicionada com sucesso.")

        # Redireciona para a página do dashboard para ver a nova entrada
        return redirect('admin_dashboard')

    corretores = Corretor.objects.all()
    clientes = Cliente.objects.all()
    correspondentes = Correspondente.objects.all()

    despesas = Transaction.objects.filter(tipo='DESPESA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    receitas = Transaction.objects.filter(tipo='RECEITA').aggregate(
        total=models.Sum('valor'))['total'] or 0
    total_receitas = Transaction.objects.filter(
        user=request.user, tipo='RECEITA').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas = Transaction.objects.filter(
        user=request.user, tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0

    saldo = receitas - despesas
    total_corretores = corretores.count()
    total_clientes = clientes.count()
    total_correspondentes = correspondentes.count()
    recent_transactions = Transaction.objects.all().order_by('-id')[:8]

    # Paginação para fixed_expenses
    paginator = Paginator(fixed_expenses, 10)  # Mostrar 10 despesas por página
    page = request.GET.get('page')
    try:
        fixed_expenses = paginator.page(page)
    except PageNotAnInteger:
        # Se a página não for um inteiro, entregue a primeira página.
        fixed_expenses = paginator.page(1)
    except EmptyPage:
        # Se a página estiver fora do intervalo (por exemplo, 9999), entregue a última página de resultados.
        fixed_expenses = paginator.page(paginator.num_pages)

    context = {
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
        'fixed_expenses': FixedExpense.objects.filter(user=request.user),
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.delete()
    return redirect('admin_dashboard')


@login_required
def add_fixed_expense(request):
    # Se a requisição for POST, tente obter as informações do formulário
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

    # Se não for POST, ou seja, se for GET, renderize o formulário para adicionar despesa
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


def mark_as_paid(request, expense_id):
    today = datetime.today()
    expense = FixedExpense.objects.get(pk=expense_id)
    expense.is_paid = True
    expense.month_paid = today.month
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


@csrf_exempt
def notify_correspondente(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        cliente_nome = data.get('cliente_nome')

        try:
            cliente = Cliente.objects.get(nome=cliente_nome)
            whatsapp_num = "kalleu313@gmail.com@c.us"  # Exemplo

            message = f'Olá, O cliente *{cliente.nome}*  foi cadastrado com sucesso no sistema. Por favor, verifique o CRM :)'

            payload = {
                'number': whatsapp_num,
                'message': message
            }

            response = requests.post(
                'http://localhost:3000/send-message', json=payload)

            if response.json().get('success'):
                return JsonResponse({"message": "Notification sent to the correspondente successfully"})
            else:
                error_message = response.json().get('error', 'Unknown error')
                return JsonResponse({"error": f"Failed to send the message on WhatsApp to the correspondente due to: {error_message}"}, status=500)
        except Cliente.DoesNotExist:
            return JsonResponse({"error": "Cliente not found"}, status=404)
