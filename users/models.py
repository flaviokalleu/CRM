from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import datetime
from django.utils import timezone
from django.utils.text import slugify
import uuid


class Proprietario(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(
        max_length=190, unique=True, verbose_name="Email")
    telefone = models.CharField(max_length=15, verbose_name="Telefone")
    endereco = models.CharField(
        max_length=300, verbose_name="Endereço")  # Use CharField
    cpf_cnpj = models.CharField(
        max_length=14, unique=True, verbose_name="CPF/CNPJ")  # Nome ajustado
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Proprietário"
        verbose_name_plural = "Proprietários"


class Contato(models.Model):
    proprietario = models.ForeignKey(
        Proprietario, on_delete=models.CASCADE, verbose_name="Proprietário")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    data_registro = models.DateTimeField(
        default=timezone.now, verbose_name="Data de Registro")

    def __str__(self):
        return self.nome


class UserAccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    action = models.TextField(null=True, blank=True)
    reference_page = models.CharField(max_length=255, null=True, blank=True)
    session_data = models.TextField(null=True, blank=True)
    referer_url = models.URLField(null=True, blank=True)
    http_method = models.CharField(max_length=10, null=True, blank=True)
    request_params = models.TextField(null=True, blank=True)
    request_body = models.TextField(null=True, blank=True)
    request_headers = models.TextField(null=True, blank=True)
    browser_info = models.TextField(null=True, blank=True)
    device_info = models.TextField(null=True, blank=True)
    os_info = models.TextField(null=True, blank=True)

    def formatted_timestamp(self):
        return self.timestamp.strftime('%d/%m/%Y %H:%M:%S')

    def __str__(self):
        return f"{self.user} - {self.action} em {self.formatted_timestamp()}"


class CustomUserManager(BaseUserManager):

    def _create_user(self, username, email, role=None, password=None, **extra_fields):
        """Creates and returns a user with an email, username and password."""
        if not email:
            raise ValueError(_('O campo email é obrigatório'))
        if not username:
            raise ValueError(_('O campo username é obrigatório'))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)

        if not password:
            password = "default_password"

        user.set_password(password)
        user.save(using=self._db)

        if role:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)

        return user

    def create_user(self, username, email, role=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, role, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(username, email, None, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(max_length=190, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)
    # Mantenha somente esta definição
    telefone = models.CharField(max_length=15, null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def is_corretor(self):
        return self.groups.filter(name="Corretores").exists()

    def is_correspondente(self):
        return self.groups.filter(name="correspondente").exists()


class TipoProcesso(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

    def obter_opcoes(self):
        if self.nome == 'novo':
            return ['Aprovado', 'Visita no imovel', 'Cartório']
        elif self.nome == 'usado':
            return ['Receber valor ', 'Cartório ', 'Entrega de chaves']
        elif self.nome == 'Agio':
            return ['Receber valor ', 'Cartório ', 'Entrega de chaves']
        else:
            return []


class OpcaoProcesso(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    tipo_processo = models.ForeignKey(TipoProcesso, on_delete=models.CASCADE)
    opcao = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.cliente.nome} - {self.tipo_processo.nome} - {self.opcao}"


class OpcaoSelecionada(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    processo = models.ForeignKey('Processo', on_delete=models.CASCADE)
    tipo_processo = models.ForeignKey('TipoProcesso', on_delete=models.CASCADE)
    opcao = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.cliente.nome} - {self.tipo_processo.nome} - {self.opcao}"


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
        ('Não Deu continuidade', 'Não Deu continuidade'),
    ]

    nome = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(
        max_length=191,  null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    corretor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="clientes", limit_choices_to={'groups__name': 'Corretores'})
    cpf = models.CharField(max_length=14,
                           null=True, blank=True)
    valor_da_renda = models.CharField(max_length=14,
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
    data_de_criacao = models.DateTimeField(auto_now_add=True)
    opcoes_processo = models.JSONField(default=list)
    tipos_processo = models.ManyToManyField(TipoProcesso)

    def get_notas(self):
        return Nota.objects.filter(cliente=self).order_by('-data_criacao')

    def notas_count(self):
        return Nota.objects.filter(cliente=self).count()

    def tem_nota_nova(self):
        return Nota.objects.filter(cliente=self, nova=True).exists()

    def __str__(self):
        return self.nome


TIPOS_PROCESSO = (
    ('usado', 'Usado'),
    ('novo', 'Novo'),
    ('agio', 'Ágio')
)


class Documento(models.Model):
    arquivo = models.FileField(upload_to='documentos/')
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="documentos")


class Correspondente(CustomUser):

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Corretores(CustomUser):

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class VendaCorretor(models.Model):
    nome = models.CharField(max_length=100)
    valor_total_pagar = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2)
    nome_corretor = models.CharField(max_length=100)
    valor_faltante = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Processo(models.Model):
    cliente = models.ForeignKey('users.Cliente', on_delete=models.CASCADE)
    tipo = models.CharField(
        max_length=5, choices=TIPOS_PROCESSO, default='novo')
    tags = models.CharField(max_length=255)
    responsavel = models.ForeignKey(
        'users.Corretores', on_delete=models.SET_NULL, null=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_finalizacao = models.DateField(null=True, blank=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    proprietario = models.ForeignKey(
        Proprietario, on_delete=models.CASCADE, verbose_name="Proprietário")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.cliente.nome)
            self.slug = f"{base_slug}-{uuid.uuid4()}"[:250]
            while Processo.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{uuid.uuid4()}"[:250]
        super().save(*args, **kwargs)


@receiver(post_save, sender=Correspondente)
def add_correspondente_to_group(sender, instance=None, created=False, **kwargs):
    if created:
        correspondente_group, _ = Group.objects.get_or_create(
            name='correspondente')
        instance.groups.add(correspondente_group)


@receiver(post_save, sender=Corretores)
def add_correspondente_to_group(sender, instance=None, created=False, **kwargs):
    if created:
        correspondente_group, _ = Group.objects.get_or_create(
            name='Corretores')
        instance.groups.add(correspondente_group)


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
        current_month = today.month
        current_year = today.year
        due_date_this_month = datetime.date(
            current_year, current_month, self.due_day)
        difference = (due_date_this_month - today).days

        # Se a diferença for negativa, verifique o próximo mês
        if difference < 0:
            # 12 vai para 1, outros meses incrementam
            next_month = (current_month % 12) + 1
            due_date_next_month = datetime.date(
                current_year if current_month != 12 else current_year + 1, next_month, self.due_day)
            difference = (due_date_next_month - today).days

        return 0 <= difference <= 3


class NotaPrivada(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)
    conteudo = models.TextField()
    # Campo novo para marcar a nota como concluída
    concluido = models.BooleanField(default=False)

    def __str__(self):
        return self.conteudo[:50]


class Nota(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    nova = models.BooleanField(default=True)

    def __str__(self):
        return f"Nota para {self.cliente.nome} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"
