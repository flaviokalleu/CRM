from django import forms
from .models import Cliente, Corretores, Correspondente, Processo, Transaction, Documento
from .models import CustomUser  # ou o nome do seu modelo de usuário
from django.contrib.auth.models import User
from .models import Proprietario, OpcaoProcesso, TipoProcesso
from django import forms
from django.core.validators import RegexValidator

class CPFForm(forms.Form):
    cpf = forms.CharField(
        validators=[RegexValidator(regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$', message='CPF inválido')]
    )

class ProprietarioForm(forms.ModelForm):
    class Meta:
        model = Proprietario
        fields = ['nome', 'email', 'telefone',
                  'endereco', 'cpf_cnpj']


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Adicione mais campos conforme necessário
        fields = ['first_name', 'last_name', 'email', 'username']


class CorretorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")

    class Meta:
        model = Corretores
        fields = ['username', 'first_name', 'last_name',
                  'email', 'telefone', 'password']


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


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
        exclude = ('documentacao','status','opcoes_processo','tipos_processo')


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['arquivo']


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
    email = forms.EmailField(max_length=254, required=True, widget=forms.EmailInput(
        attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "Este endereço de e-mail já está em uso.")
        return email


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['cliente', 'tipo', 'tags', 'responsavel',
                  'data_inicio', 'data_finalizacao']


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


