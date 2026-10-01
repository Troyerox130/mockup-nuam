from django import forms
from .models import CalificacionTributaria

class CalificacionForm(forms.ModelForm):
    class Meta:
        model = CalificacionTributaria
        fields = ['mercado', 'origen', 'periodo_comercial', 'ejercicio', 'instrumento', 'fecha_pago', 'descripcion', 'secuencia_evento']
        widgets = {
            'mercado': forms.TextInput(attrs={'class': 'form-control'}),
            'origen': forms.TextInput(attrs={'class': 'form-control'}),
            'periodo_comercial': forms.NumberInput(attrs={'class': 'form-control'}),
            'ejercicio': forms.TextInput(attrs={'class': 'form-control'}),
            'instrumento': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'secuencia_evento': forms.TextInput(attrs={'class': 'form-control'}),
        }