# service_ac/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/create_admin/', views.create_admin, name='create_admin'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/teknisi/', views.manage_teknisi, name='manage_teknisi'),
    path('admin/harga/', views.manage_harga, name='manage_harga'),
    path('api/harga/', views.api_manage_harga, name='api_manage_harga'),
    path('admin/history_service/', views.history_service, name='service_history'),

    path('admin/service/', views.manage_service, name='manage_service'),
    path('api/service/', views.api_manage_service, name='api_manage_service'),
    path('api/manage_teknisi/', views.api_manage_teknisi, name='api_manage_teknisi'),


    path('api/users/', views.user_list, name='user_list'),
    path('api/users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('teknisi/dashboard/', views.teknisi_dashboard, name='teknisi_dashboard'),
    path('teknisi/manage_jobs/', views.manage_jobs, name='manage_jobs'),
    path('api/teknisi/update_status/<int:job_id>/', views.update_status, name='update_status'),


    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/view_orders/', views.view_orders, name='view_orders'),
    path('user/profile', views.profile, name='profile'),
    path('user/order_service', views.order_service, name='order_service'),
     
    # path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'), 
    # path('teknisi/dashboard/', views.teknisi_dashboard, name='teknisi_dashboard'),
    # path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
]
