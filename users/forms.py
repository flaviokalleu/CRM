from django import forms
from .models import Cliente, Corretor, Correspondente, Transaction, Documento


class CorretorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")

    class Meta:
        model = Corretor
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
        # Exclua 'documentacao' já que estamos usando 'documentos' para lidar com múltiplos arquivos
        exclude = ('documentacao',)


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
