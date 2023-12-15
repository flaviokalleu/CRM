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

    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'email', 'telefone', 'corretor', 'cpf', 'estado_civil',
            'naturalidade', 'profissao', 'data_admissao', 'data_nascimento',
            'renda_tipo', 'possui_carteira_mais_tres_anos', 'numero_pis',
            'possui_dependente', 'documentacao', 'status', 'data_de_criacao',
            'opcoes_processo', 'tipos_processo', 'notas_count', 'tem_nota_nova'
        ]

