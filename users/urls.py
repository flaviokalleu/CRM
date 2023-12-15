from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings


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
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
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
    path('notify-correspondente/', views.notify_correspondente,
         name='notify-correspondente')
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
