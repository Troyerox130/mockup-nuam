from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
import pandas as pd
from mantenedor.models import CalificacionTributaria
from mantenedor.forms import CalificacionForm, CargaFactorForm, CargaMontoForm

# ==========================================
# FUNCIONES DE VERIFICACIÓN DE ROLES (RBAC)
# ==========================================

def es_supervisor(user):
    return user.is_superuser or user.groups.filter(name='Supervisor').exists()

def es_usuario_autorizado(user):
    return user.is_superuser or user.groups.filter(name__in=['Supervisor', 'Usuario Autorizado']).exists()


# ==========================================
# VISTAS PRINCIPALES Y OPERACIONES COMPARTIDAS
# ==========================================

@login_required
@user_passes_test(es_usuario_autorizado)
def lista_calificaciones(request):
    user_es_supervisor = es_supervisor(request.user)
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro ingresado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm()

    calificaciones = CalificacionTributaria.objects.all().order_by('-id')
    
    # Filtros
    mercado = request.GET.get('mercado')
    origen = request.GET.get('origen')
    periodo_comercial = request.GET.get('periodo_comercial')

    if mercado:
        calificaciones = calificaciones.filter(mercado=mercado)
    if origen:
        calificaciones = calificaciones.filter(origen=origen)
    if periodo_comercial:
        calificaciones = calificaciones.filter(periodo_comercial=periodo_comercial)
        
    # --- LÓGICA DE PAGINACIÓN ---
    paginator = Paginator(calificaciones, 10)  # Muestra 10 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Guardamos los filtros actuales para que no se borren al cambiar de página
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    contexto = {
        'calificaciones': page_obj,  # Enviamos la página actual en vez de todos los datos
        'form': form,
        'es_supervisor': user_es_supervisor,
        'periodo_buscado': periodo_comercial,
        'query_params': query_params.urlencode(),  # Enviamos la URL de filtros armadita
    }
    return render(request, 'mantenedor/lista.html', contexto)

@login_required
@user_passes_test(es_usuario_autorizado)
def editar_calificacion(request, pk):
    registro = get_object_or_404(CalificacionTributaria, pk=pk)
    user_es_supervisor = es_supervisor(request.user)
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro modificado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm(instance=registro)
        
    # Para la vista de fondo, cargamos la página 1
    calificaciones = CalificacionTributaria.objects.all()
    paginator = Paginator(calificaciones, 10)
    page_obj = paginator.get_page(1)
    
    return render(request, 'mantenedor/lista.html', {
        'calificaciones': page_obj,
        'form': form,
        'es_supervisor': user_es_supervisor,
        'abrir_modal_edicion': True
    })

@login_required
@user_passes_test(es_usuario_autorizado)
def copiar_calificacion(request, pk):
    registro_original = get_object_or_404(CalificacionTributaria, pk=pk)
    registro_original.pk = None
    user_es_supervisor = es_supervisor(request.user)
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=registro_original)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro copiado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm(instance=registro_original)
        
    calificaciones = CalificacionTributaria.objects.all()
    paginator = Paginator(calificaciones, 10)
    page_obj = paginator.get_page(1)
    
    return render(request, 'mantenedor/lista.html', {
        'calificaciones': page_obj,
        'form': form,
        'es_supervisor': user_es_supervisor,
        'abrir_modal_edicion': True
    })

# ==========================================
# VISTAS RESTRINGIDAS (SOLO SUPERVISOR)
# ==========================================

@login_required
def eliminar_calificacion(request, pk):
    if not es_supervisor(request.user):
        raise PermissionDenied("Acceso denegado: Operación exclusiva para el rol Supervisor.")
        
    registro = get_object_or_404(CalificacionTributaria, pk=pk)
    registro.delete()
    messages.success(request, 'Registro eliminado exitosamente.')
    return redirect('lista_calificaciones')

@login_required
def carga_factor(request):
    if not es_supervisor(request.user):
        raise PermissionDenied("Acceso denegado.")
    if request.method == 'POST':
        messages.success(request, 'Archivo de Carga x Factor procesado correctamente.')
        return redirect('lista_calificaciones')
    return redirect('lista_calificaciones')

@login_required
def carga_monto(request):
    """Procesa el archivo CSV para Carga x Monto con formato exacto, calcula proporciones y guarda masivamente"""
    if not es_supervisor(request.user):
        raise PermissionDenied("Acceso denegado: Solo un Supervisor puede realizar cargas masivas.")
        
    if request.method == 'POST' and request.FILES.get('archivo_monto'):
        archivo = request.FILES['archivo_monto']
        try:
            df = None
            encodings = ['utf-8-sig', 'latin-1', 'cp1252', 'utf-8']
            
            # Intentar leer el CSV con punto y coma (;) asegurando formato de texto
            for enc in encodings:
                try:
                    archivo.seek(0)
                    df = pd.read_csv(archivo, sep=';', encoding=enc, dtype=str)
                    if df is not None and len(df.columns) > 5 and not df.empty:
                        df.columns = df.columns.str.strip()
                        break
                except Exception:
                    continue
            
            if df is None or len(df.columns) <= 5:
                raise ValueError("El archivo CSV no es válido. Asegúrate de usar punto y coma (;) como separador.")
                
            df = df.fillna(0)
            registros_a_crear = []

            for index, row in df.iterrows():
                # 1. Calcular el "Monto Base" (Suma exacta de las columnas Monto_08 a la Monto_19)
                suma_base = 0.0
                for i in range(8, 20):
                    col_name = f"Monto_{i:02d}"
                    if col_name in df.columns:
                        val_str = str(row[col_name]).strip().replace('.', '').replace(',', '.')
                        try:
                            suma_base += float(val_str) if val_str else 0.0
                        except ValueError:
                            pass

                # 2. Calcular los 30 factores (F-08 hasta F-37) redondeados a 8 decimales
                factores_calculados = {}
                for i in range(8, 38):
                    col_name = f"Monto_{i:02d}"
                    if col_name in df.columns and suma_base > 0:
                        val_str = str(row[col_name]).strip().replace('.', '').replace(',', '.')
                        try:
                            valor_monto = float(val_str) if val_str else 0.0
                            factor_final = round(valor_monto / suma_base, 8)
                        except ValueError:
                            factor_final = 0.00000000
                    else:
                        factor_final = 0.00000000
                        
                    factores_calculados[f"factor_{i:02d}"] = factor_final

                # 3. Formatear la fecha de pago de manera segura
                fecha_pago_val = None
                raw_fecha = row.get('FEC_PAGO', '')
                if raw_fecha and str(raw_fecha).strip() not in ['', '0', 'nan']:
                    try:
                        fecha_pago_val = pd.to_datetime(raw_fecha).date()
                    except Exception:
                        fecha_pago_val = None

                # 4. Crear el objeto de base de datos
                nueva_calificacion = CalificacionTributaria(
                    ejercicio=int(row.get('EJERCICIO', 2025)) if str(row.get('EJERCICIO', '2025')).isdigit() else 2025,
                    mercado=str(row.get('MERCADO', 'ACCIONES')).strip(),
                    instrumento=str(row.get('NEMOTECNICO', 'N/A')).strip(),
                    fecha_pago=fecha_pago_val,
                    secuencia_evento=str(row.get('SEC_EVE', '')).strip(),
                    descripcion=str(row.get('DESCRIPCION', '')).strip(),
                    monto=suma_base,
                    **factores_calculados
                )
                registros_a_crear.append(nueva_calificacion)

            # Guardado masivo ultrarrápido
            CalificacionTributaria.objects.bulk_create(registros_a_crear)
            messages.success(request, f'¡Carga exitosa! Se procesaron y calcularon {len(registros_a_crear)} registros correctamente.')

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo CSV. Detalle: {str(e)}")

        return redirect('lista_calificaciones')
        
    return redirect('lista_calificaciones')