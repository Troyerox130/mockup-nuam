from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Tu login original y bonito sin intermediarios
    path('account/login/', auth_views.LoginView.as_view(template_name='mantenedor/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Rutas de tu app mantenedor
    path('', include('mantenedor.urls')),
]