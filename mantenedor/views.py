from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from .models import CalificacionTributaria
from .forms import CalificacionForm, CargaFactorForm, CargaMontoForm

def lista_calificaciones(request):
    # Toma 2025 por defecto para sincronizar con el selector
    periodo_buscado = request.GET.get('periodo_comercial', '2025')
    
    # Filtra siempre por el periodo_buscado
    calificaciones = CalificacionTributaria.objects.filter(periodo_comercial=periodo_buscado)

    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            # 1. Obtenemos la instancia sin guardarla aún en la BD
            nueva_calificacion = form.save(commit=False)
            
            # 2. AQUÍ REALIZAS TUS CÁLCULOS
            # Ejemplo: Si el factor 08 depende de una fórmula con el Monto
            # if nueva_calificacion.monto:
            #     nueva_calificacion.factor_08 = nueva_calificacion.monto * 0.15
            #     nueva_calificacion.factor_09 = nueva_calificacion.monto * 0.25
            
            # 3. Guardamos finalmente en la BD
            nueva_calificacion.save()
            
            messages.success(request, 'Registro grabado y calculado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm()
    
    return render(request, 'mantenedor/lista.html', {
        'calificaciones': calificaciones,
        'form': form,
        'periodo_buscado': periodo_buscado,
        'carga_factor_form': CargaFactorForm(
            initial={'periodo_factor': periodo_buscado}
        ),
        'carga_monto_form': CargaMontoForm(
            initial={'periodo_monto': periodo_buscado}
        ),
    })

def editar_calificacion(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=calificacion)
        if form.is_valid():
            # 1. Obtenemos la instancia sin guardarla aún en la BD
            calificacion_actualizada = form.save(commit=False)
            
            # 2. AQUÍ REALIZAS TUS CÁLCULOS
            # Ejemplo: Si el factor 08 depende de una fórmula con el Monto
            # if calificacion_actualizada.monto:
            #     calificacion_actualizada.factor_08 = calificacion_actualizada.monto * 0.15
            #     calificacion_actualizada.factor_09 = calificacion_actualizada.monto * 0.25
            
            # 3. Guardamos finalmente en la BD
            calificacion_actualizada.save()
            
            messages.success(request, 'Registro actualizado y calculado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm(instance=calificacion)
    return render(request, 'mantenedor/editar.html', {'form': form})

def copiar_calificacion(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    calificacion.pk = None
    calificacion.descripcion = f"{calificacion.descripcion} (Copia)"
    calificacion.save()
    return redirect('lista_calificaciones')

def eliminar_calificacion(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    calificacion.delete()
    return redirect('lista_calificaciones')

@require_POST
def carga_factor(request):
    form = CargaFactorForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'No se aplicó la carga por factor. Revisa los datos ingresados.')
        return redirect('lista_calificaciones')

    periodo = form.cleaned_data['periodo_factor']
    campo_factor = form.cleaned_data['campo_factor']
    valor = form.cleaned_data['valor_factor']
    actualizados = CalificacionTributaria.objects.filter(
        periodo_comercial=periodo
    ).update(**{campo_factor: valor})

    if actualizados:
        messages.success(
            request,
            f'Se actualizó el factor en {actualizados} registro(s) del período {periodo}.',
        )
    else:
        messages.warning(request, f'No hay registros para el período {periodo}.')
    return redirect('lista_calificaciones')

@require_POST
def carga_monto(request):
    form = CargaMontoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'No se aplicó la carga por monto. Revisa los datos ingresados.')
        return redirect('lista_calificaciones')

    periodo = form.cleaned_data['periodo_monto']
    valor = form.cleaned_data['valor_monto']
    actualizados = CalificacionTributaria.objects.filter(
        periodo_comercial=periodo
    ).update(monto=valor)

    if actualizados:
        messages.success(
            request,
            f'Se actualizó el monto en {actualizados} registro(s) del período {periodo}.',
        )
    else:
        messages.warning(request, f'No hay registros para el período {periodo}.')
    return redirect('lista_calificaciones')