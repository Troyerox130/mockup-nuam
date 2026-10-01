from django.db import models

class CalificacionTributaria(models.Model):
    mercado = models.CharField(max_length=50, default="ACCIONES", verbose_name="Mercado")
    origen = models.CharField(max_length=50, default="CORREDOR", verbose_name="Origen")
    periodo_comercial = models.IntegerField(default=2025, verbose_name="Periodo Comercial")
    ejercicio = models.CharField(max_length=20, verbose_name="Ejercicio")
    instrumento = models.CharField(max_length=100, verbose_name="Instrumento")
    fecha_pago = models.DateField(verbose_name="Fecha Pago")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción")
    secuencia_evento = models.CharField(max_length=50, blank=True, null=True, verbose_name="Secuencia Evento")
    
    def __str__(self):
        return f"{self.instrumento} - {self.periodo_comercial}"