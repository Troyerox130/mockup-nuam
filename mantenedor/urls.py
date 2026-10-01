from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_calificaciones, name='lista_calificaciones'),
    path('editar/<int:pk>/', views.editar_calificacion, name='editar_calificacion'),
    path('copiar/<int:pk>/', views.copiar_calificacion, name='copiar_calificacion'),
    path('eliminar/<int:pk>/', views.eliminar_calificacion, name='eliminar_calificacion'),
    path('carga-factor/', views.carga_factor, name='carga_factor'),
    path('carga-monto/', views.carga_monto, name='carga_monto'),
]