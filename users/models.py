import re
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import datetime
from django.utils import timezone
from django.utils.text import slugify
import uuid
from datetime import datetime


class Proprietario(models.Model):
    nome = models.CharField(max_length=300, verbose_name="Nome")
    email = models.EmailField(max_length=300, verbose_name="Email")
    telefone = models.CharField(max_length=300, verbose_name="Telefone")
    endereco = models.CharField(max_length=300, verbose_name="Endereço")
    cpf_cnpj = models.CharField(max_length=300, verbose_name="CPF/CNPJ")  # Modificado para max_length=18
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    documentacao = models.FileField(upload_to='proprietario/', blank=True, null=True, verbose_name="Documentacao")

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


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(max_length=190, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)
    CRECI = models.CharField(max_length=100, blank=True, null=True)
    Endereço = models.CharField(max_length=100, blank=True, null=True)
    PIX_Conta = models.CharField(max_length=100, blank=True, null=True)
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

def documento_upload_to(instance, filename):
    return f'documentos/{instance.corretor.username}/{instance.cpf}/{filename}'






class TipoProcesso(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

    def obter_opcoes(self):
        if self.nome == 'novo':
            return ['Aprovação', 'Ficha de cadastro 3B', 'Pagamento TSD', 'Fichas Caixa', 'Documentação Dep', 'Declaração Dep', 
        'Documentação imóvel', 'Damp', 'Conformidade', 'Inconforme', 'Conforme', 'Assinatura Minuta Caixa', 'Itbi', 
        'Registro', 'Comissão', 'Receber valor', 'Cartório', 'Entrega de chaves']

        elif self.nome == 'usado':
            return ['Aprovação', 'Ficha de cadastro 3B', 'Pagamento TSD', 'Fichas Caixa', 'Documentação Dep', 'Declaração Dep', 
        'Documentação imóvel', 'Damp', 'Pedido avaliação', 'Pag. avaliação', 'Avaliação feita', 'Avaliação no sistema', 
        'Vistoria engenharia', 'Conformidade', 'Inconforme', 'Conforme', 'Assinatura Minuta Caixa', 'Entrada Itbi', 
        'Pagamento Itbi', 'Recolhimento Itbi ass', 'Registro', 'Exigência', 'Registrado/Averbado', 'Matrícula Atualizada', 
        'Conformidade Garantia', 'Garantia Inconforme', 'Garantia Conforme', 'Recebimento Valores', 'Comissão', 
        'Receber valor', 'Cartório', 'Entrega de chaves']

        elif self.nome == 'Agio':
            return ['Escolha Unidade', 'Pagamento sinal', 'Verificação Parcelas', 'Verificação Cond', 'Verificação IPTU', 
        'Agendamento Cartório', 'Cessão de Direitos', 'Procuração', 'Doc identificação Autenticado', 
        'Pagamento Agio', 'Recebimento comissão', 'Receber valor', 'Cartório', 'Entrega de chaves']

        else:
            return []


class OpcaoProcesso(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    tipo_processo = models.ForeignKey(TipoProcesso, on_delete=models.CASCADE)
    opcao = models.CharField(max_length=255)
    data_selecionada = models.DateField(auto_now=False)
    def __str__(self):
        return f"{self.cliente.nome} - {self.tipo_processo.nome} - {self.opcao}"


class OpcaoSelecionada(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    processo = models.ForeignKey('Processo', on_delete=models.CASCADE)
    tipo_processo = models.ForeignKey('TipoProcesso', on_delete=models.CASCADE)
    opcao = models.CharField(max_length=255)
    data_selecionada = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.tipo_processo.nome} - {self.opcao}"

def validate_cpf(value):
    if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', value):
        raise ValidationError('CPF deve estar no formato "###.###.###-##"')
    
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
    ('aguardando_aprovacao', 'Aguardado Aprovação'),
    ('documentacao_pendente', 'Documentação Pendente'),
    ('aguardando_cancelamento_qv', 'Aguardando Cancelamento / QV'),
    ('cliente_aprovado', 'Cliente Aprovado'),
    ('reprovado', 'Cliente Reprovado'),
    ('proposta_apresentada', 'Proposta Apresentada'),
    ('visita_efetuada', 'Visita Efetuada'),
    ('nao_deu_continuidade', 'Não Deu Continuidade'),
    ('venda_concluida', 'Venda Concluída'),
    ('processo_em_aberto', 'Processo Aberto'),
    ('concluido', 'Finalizado'),
]


    nome = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=191, null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    corretor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="clientes", limit_choices_to={'groups__name': 'Corretores'})
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, validators=[validate_cpf])
    valor_da_renda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor de Renda'
    )

    estado_civil = models.CharField(
        max_length=50, choices=ESTADO_CIVIL_CHOICES, null=True, blank=True)
    naturalidade = models.CharField(max_length=100, null=True, blank=True)
    profissao = models.CharField(max_length=100, null=True, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Nascimento'
    )
    renda_tipo = models.CharField(
        max_length=20, choices=RENDA_CHOICES, null=True, blank=True)
    possui_carteira_mais_tres_anos = models.BooleanField(null=True, blank=True)
    numero_pis = models.CharField(max_length=15, null=True, blank=True)
    possui_dependente = models.BooleanField(null=True, blank=True)
    documentos_pessoais = models.FileField(upload_to=documento_upload_to, null=True, blank=True)
    extrato_bancario = models.FileField(upload_to=documento_upload_to, null=True, blank=True)
    documentos_dependente = models.FileField(upload_to=documento_upload_to, null=True, blank=True)
    documentos_conjuge = models.FileField(upload_to=documento_upload_to, null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='aguardando_aprovacao', null=True, blank=True)
    data_de_criacao = models.DateTimeField(auto_now_add=True)
    opcoes_processo = models.JSONField(default=list)
    tipos_processo = models.ManyToManyField(TipoProcesso)

    def get_notas(self):
        return Nota.objects.filter(cliente=self).order_by('-data_criacao')

    def notas_count(self):
        return Nota.objects.filter(cliente=self).count()
    @property
    def data_nascimento_ajustada(self):
        """
        Retorna a data de nascimento com 1 dia adicionado.
        """
        if self.data_nascimento:
            return self.data_nascimento + timedelta(days=1)
        return None  # Retorna None se a data de nascimento for nula

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
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(
        max_length=5, choices=TIPOS_PROCESSO, default='novo')
    tags = models.CharField(max_length=255)
    responsaveis = models.ManyToManyField(Corretores)
    data_inicio = models.DateField(null=True, blank=True)
    data_finalizacao = models.DateField(null=True, blank=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    proprietario = models.ForeignKey(
        Proprietario, on_delete=models.CASCADE, verbose_name="Proprietário")
    documentacao_imovel = models.FileField(upload_to='processo_documentacao_imovel/', null=True, blank=True)
    imoveis = models.ManyToManyField('Imovel', blank=True)
    

    def get_notas(self):
        return Nota_notification.objects.filter(processo=self).order_by('-data_criacao')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.cliente.nome if self.cliente else "")
            self.slug = f"{base_slug}-{uuid.uuid4()}"[:250]
            while Processo.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{uuid.uuid4()}"[:250]

        if not self.data_inicio:
            self.data_inicio = datetime.now()

        super().save(*args, **kwargs)

        
class Nota(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    processo = models.ForeignKey('Processo', on_delete=models.CASCADE, null=True, blank=True)
    nova = models.BooleanField(default=True)
    destinatario = models.CharField(max_length=10, choices=[('owner', 'Proprietário'), ('broker', 'Corretor')])
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notas_criadas', blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # Se o processo não foi fornecido ou é vazio, defina como None
        if not self.processo_id or self.processo_id == '':
            self.processo = None

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


class Nota_notification(models.Model):
    DESTINATARIO_CHOICES = [
        ('owner', 'Proprietário'),
        ('broker', 'Corretor'),
    ]

    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE)
    destinatario = models.CharField(max_length=10, choices=[('owner', 'Proprietário'), ('broker', 'Corretor')])
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    nova = models.BooleanField(default=True)

    def __str__(self):
        return f"Nota para {self.cliente.nome} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"



class Backup(models.Model):
    name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='backups/')
    
class Video(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    video_file = models.FileField(upload_to='videos/')
    video_url = models.URLField(blank=True)
    
class VideoView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_watched = models.PositiveIntegerField(default=0)
    total_duration = models.PositiveIntegerField(default=0)
    


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Imovel(models.Model):
    # Campos existentes
    nome_do_imovel = models.CharField(max_length=255, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50)
    valor_de_avaliacao = models.CharField(max_length=20)  # Aceitará formatos como "1.500,00"
    valor_de_venda = models.CharField(max_length=20)  # Aceitará formatos como "1.500,00"
    documentacao = models.FileField(upload_to='imovel_documentos/', blank=True, null=True)
    tags = models.ManyToManyField(Tag)  # Campo modificado para ManyToMany com a tabela Tag
    
    # Campo para imagem de capa
    imagem_de_capa = models.ImageField(upload_to='imovel_imagens/', blank=True, null=True)

    # Campo para imagens associadas
    imagens = models.ManyToManyField('Imagem', blank=True, related_name='imoveis')

    # Campo de localização
    LOCALIZACAO_CHOICES = [
        ('Valparaiso_de_Goias', 'Valparaiso de Goiás - Goiás'),
        ('Cidade_Ocidental', 'Cidade Ocidental - Goiás'),
        ('Jardim_Ingá', 'Jardim Ingá - Goias'),
        ('Luziania', 'Luziânia - Goias'),
        ('Brasilia', 'Brasília - Distrito Federal'),
    ]
    localizacao = models.CharField(max_length=50, choices=LOCALIZACAO_CHOICES)

    # Novos campos
    exclusivo = models.BooleanField(default=False, verbose_name='Exclusivo?')
    tem_inquilino = models.BooleanField(default=False, verbose_name='Tem Inquilino?')
    situacao_do_imovel = models.TextField(blank=True, null=True, verbose_name='Situação do Imóvel')
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')
    
    # Novo campo para identificar se o imóvel é novo, usado ou ágio
    STATUS_CHOICES = [
        ('NOVO', 'Novo'),
        ('USADO', 'Usado'),
        ('AGIO', 'Ágio'),
    ]
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='NOVO')

    # Novo campo para descrição do imóvel
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição do Imóvel')

    def __str__(self):
        return self.endereco


class Imagem(models.Model):
    imagem = models.ImageField(upload_to='imovel_images/', blank=True, null=True)

    def __str__(self):
        return str(self.imagem)

    
class Contrato(models.Model):
    nome = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='contratos/')
    data_upload = models.DateTimeField(auto_now_add=True)