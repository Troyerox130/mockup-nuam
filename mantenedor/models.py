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
    acogido_isfut = models.BooleanField(default=False, verbose_name="Acogido ISFUT")

    monto = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Monto",
    )
    factor_actualizacion = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        blank=True,
        null=True,
        verbose_name="Factor de Actualización",
    )
    factor_08 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_09 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_10 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_11 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_12 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_13 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_14 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_15 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_16 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_17 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_18 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_19 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_20 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_21 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_22 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_23 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_24 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_25 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_26 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_27 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_28 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_29 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_30 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_31 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_32 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_33 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_34 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_35 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_36 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    factor_37 = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)

    def __str__(self):
        return f"{self.instrumento} - {self.periodo_comercial}"