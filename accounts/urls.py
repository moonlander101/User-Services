from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth endpoints
    path('register/', views.register_view, name='register'),
    path('register/supplier/', views.register_supplier_view, name='register_supplier'),
    path('register/vendor/', views.register_customer_view, name='register_customer'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User profile endpoints
    path('me/', views.get_profile_view, name='get_profile'),
    path('me/update/', views.update_profile_view, name='update_profile'),
    path('password/change/', views.password_change_view, name='password_change'),
    path('password/reset/', views.password_reset_view, name='password_reset'),
    path('password/reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Admin endpoints
    path('admin/users/', views.admin_get_all_users, name='admin_get_all_users'),
    path('admin/users/<int:user_id>/', views.admin_update_user, name='admin_update_user'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),

    # Driver endpoints
    path('drivers/', views.get_all_drivers_view, name='get_all_drivers'),
]