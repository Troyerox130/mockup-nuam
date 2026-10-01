from django.shortcuts import get_object_or_404, render, redirect
from .models import CalificacionTributaria
from .forms import CalificacionForm

def lista_calificaciones(request):
    periodo_buscado = request.GET.get('periodo_comercial')
    
    if periodo_buscado:
        calificaciones = CalificacionTributaria.objects.filter(periodo_comercial=periodo_buscado)
    else:
        calificaciones = CalificacionTributaria.objects.all()

    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm()
    
    return render(request, 'mantenedor/lista.html', {
        'calificaciones': calificaciones,
        'form': form,
        'periodo_buscado': periodo_buscado or ''
    })

def editar_calificacion(request, pk):
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=calificacion)
        if form.is_valid():
            form.save()
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

def carga_factor(request):
    if request.method == 'POST':
        factor = request.POST.get('valor_factor')
        periodo = request.POST.get('periodo_factor')
        # Lógica de carga por factor aquí
        return redirect('lista_calificaciones')
    return redirect('lista_calificaciones')

def carga_monto(request):
    if request.method == 'POST':
        monto = request.POST.get('valor_monto')
        periodo = request.POST.get('periodo_monto')
        # Lógica de carga por monto aquí
        return redirect('lista_calificaciones')
    return redirect('lista_calificaciones')