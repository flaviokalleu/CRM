from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
import datetime
from django import forms
from django.conf import settings
from django.contrib.auth.models import User


class UserAccessLog(models.Model):
    # Referência a AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # NOTA: Veja o ponto 2 acima
    mac_address = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    browser_info = models.TextField(null=True, blank=True)
    action = models.TextField(null=True, blank=True)


class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O campo email é obrigatório')
        if not username:
            raise ValueError('O campo username é obrigatório')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)

        if not password:
            password = "default_password"

        user.set_password(password)
        user.save(using=self._db)

        # Adicionando o usuário ao grupo 'Corretores' após a sua criação
        corretores_group, _ = Group.objects.get_or_create(name='Corretores')
        user.groups.add(corretores_group)

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

    def create_corretor(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        # Adicione um campo personalizado "is_corretor" para distinguir corretor de outros usuários
        extra_fields.setdefault('is_corretor', True)
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, null=True)

    email = models.EmailField(max_length=190, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
    )

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    is_corretor = models.BooleanField(default=False)

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        abstract = True


class Corretor(CustomUser):
    telefone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


@receiver(post_save, sender=Corretor)
def create_corretor_group_and_permissions(sender, instance=None, created=False, **kwargs):
    if created:
        corretores_group, _ = Group.objects.get_or_create(name='Corretores')
        add_cliente_permission = Permission.objects.get(codename='add_cliente')
        corretores_group.permissions.add(add_cliente_permission)


class Cliente(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ('solteiro', 'Solteiro'),
        ('casado', 'Casado'),
        ('divorciado', 'Divorciado'),
        ('viuvo', 'Viúvo'),
        ('uniao_estavel', 'União Estável'),
    ]

    RENDA_CHOICES = [
        ('formal', 'Formal'),
        ('informal', 'Informal'),
        ('mista', 'Mista')
    ]
    STATUS_CHOICES = [
        ('aguardando_aprovacao', 'Aguardando Aprovação'),
        ('documentacao_pendente', 'Documentação Pendente'),
        ('aguardando_cancelamento_qv', 'Aguardando Cancelamento QV'),
        ('cliente_aprovado', 'Cliente Aprovado'),
        ('proposta_apresentada', 'Proposta Apresentada'),
        ('visita_efetuada', 'Visita Efetuada'),
        ('fechamento_proposta', 'Fechamento Proposta'),
        ('pagamento_tsd', 'Pagamento TSD'),
        ('conformidade', 'Conformidade'),
        ('assinatura_minuta_caixa', 'Assinatura Minuta Caixa'),
        ('comissao_recebida', 'Comissão Recebida'),
        ('concluido', 'Concluído'),
        ('reprovado', 'Reprovado'),
    ]

    nome = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(
        max_length=191, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    corretor = models.ForeignKey(
        Corretor, on_delete=models.SET_NULL, null=True, blank=True, related_name="clientes")
    cpf = models.CharField(max_length=14, unique=True,
                           null=True, blank=True)  # formato 000.000.000-00
    estado_civil = models.CharField(
        max_length=50, choices=ESTADO_CIVIL_CHOICES, null=True, blank=True)
    naturalidade = models.CharField(max_length=100, null=True, blank=True)
    profissao = models.CharField(max_length=100, null=True, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    renda_tipo = models.CharField(
        max_length=20, choices=RENDA_CHOICES, null=True, blank=True)
    possui_carteira_mais_tres_anos = models.BooleanField(null=True, blank=True)
    numero_pis = models.CharField(max_length=15, null=True, blank=True)
    possui_dependente = models.BooleanField(null=True, blank=True)
    documentacao = models.FileField(
        upload_to='documentos/', null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='aguardando_aprovacao', null=True, blank=True)

    def __str__(self):
        return self.nome


class Documento(models.Model):
    arquivo = models.FileField(upload_to='documentos/')
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="documentos")


class Correspondente(CustomUser):
    telefone = models.CharField(max_length=15)
    # Temporariamente define um valor padrão
    password = models.CharField(max_length=128, default='default_password')

    class Meta:
        db_table = 'users_correspondente'


@receiver(post_save, sender=Correspondente)
def add_correspondente_to_group(sender, instance=None, created=False, **kwargs):
    if created:
        correspondente_group, _ = Group.objects.get_or_create(
            name='correspondente')
        instance.groups.add(correspondente_group)


@receiver(post_save, sender=Corretor)
def create_corretor_group_and_permissions(sender, instance=None, created=False, **kwargs):
    if created:
        corretores_group, _ = Group.objects.get_or_create(name='Corretores')
        add_cliente_permission = Permission.objects.get(codename='add_cliente')
        corretores_group.permissions.add(add_cliente_permission)
        instance.groups.add(corretores_group)


class Transaction(models.Model):
    TIPOS = (
        ('DESPESA', 'Despesa'),
        ('RECEITA', 'Receita'),
    )
    tipo = models.CharField(max_length=50, choices=TIPOS)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Adicionando o campo de usuário
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    class Meta:
        db_table = 'users_transaction'  # Define o nome da tabela


class FixedExpense(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    # De 1 a 31, representando o dia do vencimento
    due_day = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    month_paid = models.PositiveIntegerField(
        null=True, blank=True)  # Mês em que foi paga

    def __str__(self):
        return self.description

    def is_due_soon(self):
        today = datetime.date.today()
        difference = (self.due_date - today).days
        return 0 <= difference <= 3
