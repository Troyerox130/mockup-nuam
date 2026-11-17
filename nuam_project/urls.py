from django.contrib import admin
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas oficiales del 2FA importadas directamente
    path('', include(tf_urls)),
    
    # Rutas de tu app mantenedor
    path('', include('mantenedor.urls')),
]