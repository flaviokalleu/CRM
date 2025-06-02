from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from .views import adicionar_imovel, assistir_videos, cliente_processo, concluir_processo, deletar_corretor, deletar_pagina_pdf, deletar_proprietario, delete_video, download_imagens_view, editar_cliente, editar_pdf, editar_proprietario, excluir_imovel,lista_imoveis, lista_processos, registrar_visualizacao, send_whatsapp_notification, nova_nota_view, upload_video, visualizar_documentacao, visualizar_pagina_pdf
from .views import financas_view, deletar_cliente, is_correspondent
from .views import excluir_nota_notification
from django.conf.urls.static import static
from .views import deletar_processo,enviar_mensagem_correspondente
from .views import settings_page, download_backup, restore_backup
from django.urls import path,re_path
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns # new
from django.conf import settings
from django.views.static import serve


urlpatterns = [

     path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('imoveis/', views.allimoveis, name='allimoveis'),
    path('imovel/<int:imovel_id>/', views.detalhes_imovel, name='detalhes_imovel'),

    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.redirect_to_dashboard, name='dashboard_redirect'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('broker_dashboard/', views.broker_dashboard, name='broker_dashboard'),
    path('correspondent_dashboard/', views.correspondent_dashboard,
         name='correspondent_dashboard'),
    path('cadastro-corretores/', views.cadastro_corretores,
         name='cadastro_corretores'),
    path('cadastro-correspondentes/', views.cadastro_correspondentes,
         name='cadastro_correspondentes'),
    path('consulta-cpf/', views.consulta_cpf, name='consulta_cpf'),
    path('delete_transaction/<int:transaction_id>/',
         views.delete_transaction, name='delete_transaction'),
    path('add_fixed_expense/', views.add_fixed_expense, name='add_fixed_expense'),
    path('mark-as-paid/<int:expense_id>/',
         views.mark_as_paid, name='mark_as_paid'),
    path('toggle_expense_status/<int:expense_id>/',
         views.toggle_expense_status, name='toggle_expense_status'),
    path('delete_expense/<int:expense_id>/',
         views.delete_expense, name='delete_expense'),
    path('cliente/create/', views.cliente_create, name='cliente-create'),
    path('lista-clientes/', views.lista_de_clientes, name='lista_clientes'),
    path('lista-corretores/', views.lista_de_corretores, name='lista_corretores'),
    re_path(r'^$', RedirectView.as_view(url='login/', permanent=False)),
    path('consultacpf/', views.consulta_cpf, name="consulta_cpf"),
    path('atualizar-status-cliente/', views.atualizar_status_cliente,
         name='atualizar-status-cliente'),
    path('send-notification/', views.send_notification, name='send-notification'),
    path('notify-correspondente/', views.send_notification_to_correspondente,
         name='notify-correspondente'),
    path('listadecorretores/', views.lista_de_corretores, name='listadecorretores'),
    path('settings/', views.settings_view, name='settings'),
    path('proprietarios/', views.lista_proprietarios, name='lista_proprietarios'),
    path('adicionar_proprietario/', views.adicionar_proprietario,
         name='adicionar_proprietario'),
    path('adicionar_nota/', views.adicionar_nota, name='adicionar_nota'),
    path('editar_nota/<int:nota_id>/', views.editar_nota, name='editar_nota'),
    path('concluir_nota/<int:nota_id>/',
         views.concluir_nota, name='concluir_nota'),
    path('deletar_nota/<int:nota_id>/', views.deletar_nota, name='deletar_nota'),
    path('processos/', lista_processos, name='lista_processos'),
path('proprietarios/editar/<int:proprietario_id>/', editar_proprietario, name='editar_proprietario'),
    path('processos/adicionar/', views.add_processo, name='add_processo'),
    path('cliente_processo/<int:cliente_id>/',
         cliente_processo, name='cliente_processo'),
    path('cliente/<int:cliente_id>/processo/<int:processo_id>/',
         views.detalhes_do_processo, name='detalhes_do_processo'),
    path('adicionar-nota-cliente/', views.adicionar_nota_cliente,
         name='adicionar-nota-cliente'),
    path('deletar-nota-cliente/<int:nota_id>/',
         views.deletar_nota_cliente, name='deletar_nota_cliente'),
    path('atualizar-cliente/<int:client_id>/',
         views.atualizar_cliente, name='atualizar_cliente'),
    path('editar-corretor/<int:corretor_id>/', views.editar_corretor_view, name='editar_corretor'),
    path('financas/delete_expense/<int:expense_id>/',
         views.delete_expense, name='delete_expense'),
    path('financas/', financas_view, name='financas_view'),

    path('deletar_cliente/<int:cliente_id>/',
         deletar_cliente, name='deletar_cliente'),
    path('deletar_venda/<int:venda_id>/',
         views.deletar_venda, name='deletar_venda'),
    path('is_correspondent/', is_correspondent, name='is_correspondent'),
    path('clientes/', views.lista_de_clientes, name='lista_de_clientes'),
    path('processos/deletar/<int:processo_id>/', deletar_processo, name='deletar_processo'),
    path('backup/', settings_page, name='settings_page'),
    path('backup/download/<int:backup_id>/', download_backup, name='download_backup'),
    path('backup/restore/<int:backup_id>/', restore_backup, name='restore_backup'),
  
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('nova-nota/<int:cliente_id>/<int:processo_id>/', nova_nota_view, name='nova_nota'),
    path('enviar-mensagem-whatsapp/<int:cliente_id>/', send_whatsapp_notification, name='enviar_mensagem_whatsapp'),
    path('excluir-nota-notification/<int:nota_id>/', excluir_nota_notification, name='excluir_nota_notification'),
    path('enviar-mensagem-correspondente/', enviar_mensagem_correspondente, name='enviarmensagemcorrespondente'),
path('deletar_proprietario/<int:proprietario_id>/', deletar_proprietario, name='deletar_proprietario'),
path('finalizar-processo/<int:processo_id>/', views.finalizar_processo, name='finalizar_processo'),
path('editar-cliente/<int:cliente_id>/', editar_cliente, name='editar_cliente'),
path('proprietarios/editar/<int:proprietario_id>/', editar_proprietario, name='editar_proprietario'),
path('upload/', upload_video, name='upload_video'),
path('assistir/', assistir_videos, name='assistir_videos'),
path('registrar_inicio_video/', registrar_visualizacao, name='registrar_inicio_video'),
path('delete_video/', delete_video, name='delete_video'),
path('atualizar-corretor/<int:corretor_id>/', views.atualizar_corretor_view, name='atualizar_corretor'),
path('deletar_corretor/<int:corretor_id>/', deletar_corretor, name='deletar_corretor'),
path('adicionar_imovel/', adicionar_imovel, name='adicionar_imovel'),
path('lista_imoveis/', lista_imoveis, name='lista_imoveis'),
path('download_imagens/<int:imovel_id>/', download_imagens_view, name='download_imagens'),
path('excluir_imovel/<int:imovel_id>/', excluir_imovel, name='excluir_imovel'),
path('visualizar-pagina-pdf/<int:cliente_id>/<int:pagina_numero>/<str:tipo_documento>/', views.visualizar_pagina_pdf, name='visualizar_pagina_pdf'),

path('deletar-pagina-pdf/<int:cliente_id>/<int:pagina_numero>/<str:tipo_documento>/', views.deletar_pagina_pdf, name='deletar_pagina_pdf'),

path('concluir_processo/<int:cliente_id>/', concluir_processo, name='concluir_processo'),
path('editar-pdf/<int:cliente_id>/<slug:tipo_documento>/', editar_pdf, name='editar_pdf'),
path('contratos/', views.lista_contratos, name='lista_contratos'),
path('contratos/adicionar/', views.adicionar_contrato, name='adicionar_contrato'),
path('contratos/editar/<int:contrato_id>/', views.editar_contrato, name='editar_contrato'),
path('excluir_contrato/<int:contrato_id>/', views.excluir_contrato, name='excluir_contrato'),
path('download_contrato/<int:contrato_id>/', views.download_contrato, name='download_contrato'),
path('processo/editar/<int:processo_id>/', views.editar_processo, name='editar_processo'),
path('visualizar_documentacao/<int:proprietario_id>/', visualizar_documentacao, name='visualizar_documentacao'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#handler404 = error_404_view
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

