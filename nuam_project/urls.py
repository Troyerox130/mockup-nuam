from django.contrib import admin
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas oficiales del 2FA
    path('', include(tf_urls)),
    
    # Ruta para que el botón "Cerrar sesión" de tu navbar no explote
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Rutas de tu app mantenedor
    path('', include('mantenedor.urls')),
]