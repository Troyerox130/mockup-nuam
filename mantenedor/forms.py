from django import forms
from .models import CalificacionTributaria

class CalificacionForm(forms.ModelForm):
    class Meta:
        model = CalificacionTributaria
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Asignar clases de Bootstrap a todos los campos
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-sm'

        # Asignar clase de checkbox solo a 'acogido_isfut'
        if 'acogido_isfut' in self.fields:
            self.fields['acogido_isfut'].widget.attrs['class'] = 'form-check-input mt-0'
            
        # 2. Valores por defecto (para no ingresar manualmente)
        if not self.instance.pk: # Solo si es un registro nuevo
            self.initial['mercado'] = 'AC'
            self.initial['instrumento'] = 'JEEP'
            self.initial['fecha_pago'] = '2025-01-02'
            self.initial['secuencia_evento'] = '100000809'
            self.initial['periodo_comercial'] = 2025
            self.initial['descripcion'] = 'JEEP ACC 1X1'
            self.initial['origen'] = 'CORREDOR'

        # 3. Etiquetas descriptivas según el Mockup
        self.fields['factor_08'].label = 'Factor-08 No Constitutiva de Renta No Acogido a Impto.'
        self.fields['factor_09'].label = 'Factor-09 Impto. 1ra Categ. Afecto Gl. Comp. Con Devolución'
        self.fields['factor_10'].label = 'Factor-10 Impuesto Tasa Adicional Exento Art. 21'
        self.fields['factor_11'].label = 'Factor-11 Incremento Impuesto 1ra Categoría'
        self.fields['factor_12'].label = 'Factor-12 Impto. 1ra Categ. Exento Gl. Comp. Con Devolución'
        self.fields['factor_13'].label = 'Factor-13 Impto. 1ra Categ. Afecto Gl. Comp. Sin Devolución'
        self.fields['factor_14'].label = 'Factor-14 Impto. 1ra Categ. Exento Gl. Comp. Sin Devolución'
        self.fields['factor_15'].label = 'Factor-15 Impto. Créditos pro Impuestos Externos'
        self.fields['factor_16'].label = 'Factor-16 No Constitutiva de Renta Acogido a Impto.'
        self.fields['factor_17'].label = 'Factor-17 No Constitutiva de Renta Devolución de Capital Art.17'
        self.fields['factor_19'].label = 'Factor-19A Ingreso no Constitutivos de Renta'
        self.fields['factor_20'].label = 'Factor-20 Sin Derecho a Devolucion'
        self.fields['factor_21'].label = 'Factor-21 Con Derecho a Devolucion'
        self.fields['factor_22'].label = 'Factor-22 Sin Derecho a Devolucion'
        self.fields['factor_23'].label = 'Factor-23 Con Derecho a Devolucion'
        self.fields['factor_24'].label = 'Factor-24 Sin Derecho a Devolucion'
        self.fields['factor_25'].label = 'Factor-25 Con Derecho a Devolucion'
        self.fields['factor_26'].label = 'Factor-26 Sin Derecho a Devolucion'
        self.fields['factor_27'].label = 'Factor-27 Con Derecho a Devolucion'
        self.fields['factor_28'].label = 'Factor-28 Credito por IPE'
        self.fields['factor_29'].label = 'Factor-29 Sin Derecho a Devolucion'
        self.fields['factor_30'].label = 'Factor-30 Con Derecho a Devolucion'
        self.fields['factor_31'].label = 'Factor-31 Sin Derecho a Devolucion'
        self.fields['factor_32'].label = 'Factor-32 Con Derecho a Devolucion'
        self.fields['factor_33'].label = 'Factor-33 Credito por IPE'
        self.fields['factor_34'].label = 'Factor-34 Cred. Por Impto. Tasa Adicional, Ex Art. 21 LIR'
        self.fields['factor_35'].label = 'Factor-35 Tasa Efectiva Del Cred. Del FUT (TEF)'
        self.fields['factor_36'].label = 'Factor-36 Tasa Efectiva Del Cred. Del FUNT (TEX)'
        self.fields['factor_37'].label = 'Factor-37 Devolucion de Capital Art. 17 num 7 LIR'
        
        # Ajustar el widget de fecha
        self.fields['fecha_pago'].widget = forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})


# ==========================================
# CLASES DE CARGA MASIVA RESTAURADAS
# ==========================================

FACTOR_CHOICES = [
    ('factor_actualizacion', 'Factor de Actualización'),
    *[(f'factor_{number:02d}', f'Factor-{number:02d}') for number in range(8, 38)],
]

class CargaFactorForm(forms.Form):
    periodo_factor = forms.IntegerField(
        min_value=1,
        label='Periodo Comercial',
        initial=2025,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
    )
    campo_factor = forms.ChoiceField(
        choices=FACTOR_CHOICES,
        label='Factor a actualizar',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    valor_factor = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        label='Valor del Factor',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'step': '0.00000001',
            'placeholder': 'Ej. 1.05000000',
        }),
    )

class CargaMontoForm(forms.Form):
    periodo_monto = forms.IntegerField(
        min_value=1,
        label='Periodo Comercial',
        initial=2025,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
    )
    valor_monto = forms.DecimalField(
        max_digits=18,
        decimal_places=2,
        label='Valor del Monto',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'step': '0.01',
            'placeholder': 'Ej. 50000.00',
        }),
    )