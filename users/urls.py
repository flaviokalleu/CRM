from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings
from .views import cliente_processo
from .views import financas_view, deletar_cliente, is_correspondent

urlpatterns = [


    path('login/', views.login_view, name='login'),

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
    path('processos/', views.lista_processos, name='lista_processos'),
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
    path('atualizar-corretor/<int:corretor_id>/',
         views.atualizar_corretor, name='atualizar_corretor'),
    path('admin_dashboard/delete_expense/<int:expense_id>/',
         views.delete_expense, name='delete_expense'),
    path('financas/', financas_view, name='financas_view'),

    path('deletar_cliente/<int:cliente_id>/',
         deletar_cliente, name='deletar_cliente'),
    path('deletar_venda/<int:venda_id>/',
         views.deletar_venda, name='deletar_venda'),
    path('is_correspondent/', is_correspondent, name='is_correspondent'),
    path('clientes/', views.lista_de_clientes, name='lista_de_clientes'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
