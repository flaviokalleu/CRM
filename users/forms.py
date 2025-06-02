import os
from django import forms
from .models import Cliente, Contrato, Corretores, Correspondente, Imovel, Processo, Tag, Transaction, Documento, Video
from .models import CustomUser  # ou o nome do seu modelo de usuário
from django.contrib.auth.models import User
from .models import Proprietario, OpcaoProcesso, TipoProcesso
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django import forms
from django.forms.widgets import ClearableFileInput
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

class CronometroForm(forms.Form):
    cronometro_value = forms.CharField()
    processo_id = forms.IntegerField(widget=forms.HiddenInput())

class CPFForm(forms.Form):
    cpf = forms.CharField(
        validators=[RegexValidator(regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$', message='CPF inválido')]
    )

class ProprietarioForm(forms.ModelForm):
    class Meta:
        model = Proprietario
        fields = ['nome', 'email', 'telefone', 'endereco', 'cpf_cnpj', 'documentacao']
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set all fields as not required
        for field_name, field in self.fields.items():
            field.required = False

class MultipleFileInput(ClearableFileInput):
    """
    A widget for multiple file inputs.
    """
    def render(self, name, value, attrs=None, renderer=None):
        if value is not None and not isinstance(value, (list, tuple)):
            value = [value]
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if 'multiple' not in final_attrs:
            final_attrs['multiple'] = True
        output = []
        for v in value:
            output.append(super().render(name, v, final_attrs, renderer=renderer))
        return mark_safe(''.join(output))

class ProprietarioEditForm(forms.ModelForm):
    documentacao = forms.FileField(required=False, widget=MultipleFileInput)

    class Meta:
        model = Proprietario
        fields = ['nome', 'email', 'telefone', 'endereco', 'cpf_cnpj', 'documentacao']

    def __init__(self, *args, **kwargs):
        super(ProprietarioEditForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.required = False

    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data['cpf_cnpj']
        # Remover qualquer pontuação do CPF/CNPJ
        cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
        return cpf_cnpj

    def save(self, commit=True):
        proprietario = super().save(commit=False)

        if commit:
            proprietario.save()

        if self.files:
            base_folder_path = os.path.join("media", "proprietario", proprietario.nome)
            os.makedirs(base_folder_path, exist_ok=True)

            for documento in self.files.getlist('documentacao'):
                document_path = os.path.join(base_folder_path, documento.name)
                with open(document_path, 'wb+') as destination:
                    for chunk in documento.chunks():
                        destination.write(chunk)

        return proprietario


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Adicione mais campos conforme necessário
        fields = ['username', 'first_name', 'last_name',
                  'email', 'telefone','CRECI', 'Endereço', 'PIX_Conta']


class CorretorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")

    class Meta:
        model = Corretores
        fields = ['username', 'first_name', 'last_name',
                  'email', 'telefone', 'password', 'CRECI', 'Endereço', 'PIX_Conta']



class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class FinalizarProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = []  # Deixe isso vazio para não adicionar campos extras ao formulário

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicione um campo oculto para o processo_id
        self.fields['processo_id'] = forms.IntegerField(widget=forms.HiddenInput())

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ClienteForm(forms.ModelForm):
    documentos = MultipleFileField(required=False)

    class Meta:
        model = Cliente
        exclude = ('documentacao','opcoes_processo','tipos_processo')
       

class ClienteForm2(forms.ModelForm):
    class Meta:
        model = Cliente
        exclude = ['status', 'aguardado_aprovacao', 'opcoes_processo', 'tipos_processo','corretor']

    valor_da_renda = forms.DecimalField(
        label='Valor de Renda',
        max_digits=10,
        decimal_places=2,
        localize=True,  # Adiciona separadores de milhares e vírgulas
        widget=forms.TextInput(attrs={'placeholder': 'R$ 0,00'}),
    )

    data_nascimento = forms.DateField(
        label='Data de Nascimento',
        input_formats=['%d/%m/%Y'],  # Define o formato esperado da data
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'placeholder': 'DD/MM/AAAA'}),
    )

 
class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['arquivo']
        
class DocumentUploadForm(forms.Form):
    documentos_pessoais = forms.FileField(required=False)
    extrato_bancario = forms.FileField(required=False)
    documentos_dependente = forms.FileField(required=False)
    documentos_conjuge = forms.FileField(required=False)


# CorrespondenteForm
class CorrespondenteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")

    class Meta:
        model = Correspondente
        fields = ['username', 'first_name', 'last_name',
                  'email', 'telefone', 'password']

# TransactionForm


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['tipo', 'valor', 'description']
        labels = {
            'tipo': 'Tipo',
            'valor': 'Valor',
            'description': 'Descrição',
        }
        widgets = {
            'tipo': forms.Select(choices=[('DESPESA', 'Despesa'), ('RECEITA', 'Receita')]),
        }


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(max_length=190, required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    CRECI = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    Endereco = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    PIX_Conta = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'CRECI', 'Endereco', 'PIX_Conta', 'telefone')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este endereço de e-mail já está em uso.")
        return email

class CorretorEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'CRECI', 'Endereço', 'PIX_Conta', 'telefone')


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['cliente', 'proprietario', 'tipo', 'imoveis', 'tags', 'responsaveis']
    
    # Sobrescrever o campo tags para torná-lo não obrigatório
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'alguma-classe'}))

    def __init__(self, *args, **kwargs):
        super(ProcessoForm, self).__init__(*args, **kwargs)
        # Outra maneira de adicionar classes do TailwindCSS diretamente no Python
        self.fields['cliente'].widget.attrs.update({'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-black leading-tight focus:outline-none focus:shadow-outline'})
        # Repita para os outros campos conforme necessário


class OpcoesForm(forms.Form):
    opcoes_processo = forms.MultipleChoiceField(
        choices=[], widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, tipos_processo=None, opcoes_selecionadas=None, **kwargs):
        super(OpcoesForm, self).__init__(*args, **kwargs)

        opcoes_choices = [
            (opcao, opcao) for tipo_processo in tipos_processo for opcao in tipo_processo.obter_opcoes()]
        self.fields['opcoes_processo'].choices = opcoes_choices

        if opcoes_selecionadas:
            opcoes_selecionadas_vals = [opcao.opcao for opcao in opcoes_selecionadas]
            self.fields['opcoes_processo'].initial = opcoes_selecionadas_vals



class DeletarProcessoForm(forms.Form):
    confirmacao = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class UploadBackupForm(forms.Form):
    file = forms.FileField()
    
class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file', 'video_url']
        

class ImovelForm(forms.ModelForm):
    # Defina o campo para tags
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False, widget=forms.SelectMultiple(attrs={'class': 'p-2 border rounded-md', 'placeholder': 'Insira suas tags separadas por vírgula'}))

    class Meta:
        model = Imovel
        fields = ['nome_do_imovel', 'endereco', 'tipo', 'valor_de_avaliacao', 'valor_de_venda', 'documentacao', 'imagem_de_capa', 'imagens', 'localizacao', 'exclusivo', 'tem_inquilino', 'situacao_do_imovel', 'observacoes', 'tags', 'descricao']
        
        # Personalize os rótulos dos campos, se necessário
        labels = {
            'nome_do_imovel': 'Nome do Imóvel',
            'endereco': 'Endereço',
            'tipo': 'Tipo',
            'valor_de_avaliacao': 'Valor de Avaliação',
            'valor_de_venda': 'Valor de Venda',
            'documentacao': 'Documentação',
            'imagens': 'Imagens',
            'imagem_de_capa': 'Imagem de Capa',
            'exclusivo': 'Exclusivo?',
            'tem_inquilino': 'Tem Inquilino?',
            'situacao_do_imovel': 'Situação do Imóvel',
            'observacoes': 'Observações',
            'descricao': 'Descrição do Imóvel',  # Adicionado para o campo de descrição
        }
    
    # Não use 'ClearableFileInput' para 'documentacao'
    widgets = {
        'documentacao': forms.FileInput(attrs={'accept': 'application/pdf,image/*'}),  # Aceita arquivos PDF e imagens
    }
    valor_de_avaliacao = forms.CharField(max_length=20, required=False)  # Não é mais obrigatório
    valor_de_venda = forms.CharField(max_length=20, required=False)  # Não é mais obrigatório

    exclusivo = forms.BooleanField(required=False, widget=forms.Select(choices=[(True, 'Sim'), (False, 'Não')]))
    tem_inquilino = forms.BooleanField(required=False, widget=forms.Select(choices=[(True, 'Sim'), (False, 'Não')]))

    def clean_valor_de_avaliacao(self):
        valor_de_avaliacao = self.cleaned_data.get('valor_de_avaliacao')
        # Remover possíveis pontos de milhares e substituir vírgula por ponto
        valor_de_avaliacao = valor_de_avaliacao.replace('.', '').replace(',', '.')
        try:
            valor_de_avaliacao = float(valor_de_avaliacao)
        except ValueError:
            raise ValidationError('Valor de avaliação inválido')
        return valor_de_avaliacao

    def clean_valor_de_venda(self):
        valor_de_venda = self.cleaned_data.get('valor_de_venda')
        # Remover possíveis pontos de milhares e substituir vírgula por ponto
        valor_de_venda = valor_de_venda.replace('.', '').replace(',', '.')
        try:
            valor_de_venda = float(valor_de_venda)
        except ValueError:
            raise ValidationError('Valor de venda inválido')
        return valor_de_venda

    
    
class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['nome', 'arquivo']
        
class AnexarPDFForm(forms.Form):
    pdf = forms.FileField(label='Selecione o PDF', widget=forms.ClearableFileInput(attrs={'accept': '.pdf'}))