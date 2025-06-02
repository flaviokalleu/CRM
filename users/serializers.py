from rest_framework import serializers
from .models import Cliente, CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name']

class ClienteSerializer(serializers.ModelSerializer):
    corretor = CustomUserSerializer(read_only=True)
    notas_count = serializers.IntegerField(read_only=True)
    tem_nota_nova = serializers.BooleanField(read_only=True)

    documentos_pessoais = serializers.SerializerMethodField()
    extrato_bancario = serializers.SerializerMethodField()
    documentos_dependente = serializers.SerializerMethodField()
    documentos_conjuge = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'email', 'telefone', 'corretor', 'cpf', 'estado_civil',
            'naturalidade', 'profissao', 'data_admissao', 'data_nascimento',
            'renda_tipo', 'possui_carteira_mais_tres_anos', 'numero_pis',
            'possui_dependente', 'status', 'data_de_criacao',
            'opcoes_processo', 'tipos_processo', 'notas_count', 'tem_nota_nova',
            'documentos_pessoais', 'extrato_bancario', 'documentos_dependente', 'documentos_conjuge'
        ]

    def get_documentos_pessoais(self, obj):
        return obj.documentos_pessoais.url if obj.documentos_pessoais else None

    def get_extrato_bancario(self, obj):
        return obj.extrato_bancario.url if obj.extrato_bancario else None

    def get_documentos_dependente(self, obj):
        return obj.documentos_dependente.url if obj.documentos_dependente else None

    def get_documentos_conjuge(self, obj):
        return obj.documentos_conjuge.url if obj.documentos_conjuge else None
