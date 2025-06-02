from django import template
from django.http import FileResponse
from django.views.decorators.clickjacking import xframe_options_exempt

register = template.Library()

@register.simple_tag
def obter_opcoes_processo_para_cliente(tipo_processo, cliente):
    return tipo_processo.opcoes_processo(cliente)

@register.filter
def is_corretor(user):
    return user.groups.filter(name='Corretores').exists()

@register.filter
def is_correspondente(user):
    return user.groups.filter(name='correspondente').exists()

@register.filter
def is_admin(user):
    return user.is_superuser