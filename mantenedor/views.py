from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
import pandas as pd
from mantenedor.models import CalificacionTributaria
from mantenedor.forms import CalificacionForm
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime


def obtener_texto_csv(row, campo, fila, max_length=None):
    valor = row.get(campo, '')
    if pd.isna(valor):
        valor = ''
    valor = str(valor).strip()
    if not valor:
        raise ValueError(f"El campo '{campo}' está vacío.")
    if max_length and len(valor) > max_length:
        raise ValueError(f"El campo '{campo}' supera el máximo de {max_length} caracteres. Recibido: {len(valor)}.")
    return valor

def convertir_isfut(valor):
    valor = str(valor).strip().upper()
    equivalencias = {'S': True, 'SI': True, 'N': False, 'NO': False}
    if valor not in equivalencias:
        raise ValueError(f"Valor inválido para acogido_isfut: '{valor}'. Utiliza S, SI, N o NO.")
    return equivalencias[valor]

def convertir_entero_csv(valor, campo, max_length=None):
    valor = str(valor).strip()
    if not valor.isdigit():
        raise ValueError(f"El campo '{campo}' debe contener un número entero.")
    if max_length and len(valor) > max_length:
        raise ValueError(f"El campo '{campo}' supera el máximo de {max_length} dígitos.")
    return int(valor)

def convertir_decimal_csv(valor, campo, decimales, max_digits, minimo=None, maximo=None, redondear=False):
    valor = str(valor).strip()
    if not valor:
        raise ValueError(f"El campo '{campo}' está vacío.")
    if ',' in valor and '.' not in valor and valor.count(',') == 1:
        valor = valor.replace(',', '.')
    try:
        numero = Decimal(valor)
    except InvalidOperation:
        raise ValueError(f"El campo '{campo}' contiene un valor decimal inválido: '{valor}'.")
    if not numero.is_finite():
        raise ValueError(f"El campo '{campo}' debe ser un número finito.")
    if minimo is not None and numero < minimo:
        raise ValueError(f"El campo '{campo}' no puede ser negativo.")
    if maximo is not None and numero > maximo:
        raise ValueError(f"El campo '{campo}' no puede superar {maximo}.")
    
    precision = Decimal('1').scaleb(-decimales)
    if redondear:
        numero = numero.quantize(precision, rounding=ROUND_HALF_UP)
    elif numero.as_tuple().exponent < -decimales:
        raise ValueError(f"El campo '{campo}' permite máximo {decimales} decimales.")

    digitos = len(numero.as_tuple().digits)
    exponente = numero.as_tuple().exponent
    digitos_enteros = max(digitos + exponente, 0)
    if digitos_enteros > max_digits - decimales:
        raise ValueError(f"El campo '{campo}' supera la precisión máxima permitida.")
    return numero

def leer_csv_con_separador(archivo, minimo_columnas=6):
    separadores = [';', ',']
    encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']
    for separador in separadores:
        for encoding in encodings:
            try:
                archivo.seek(0)
                df = pd.read_csv(archivo, sep=separador, encoding=encoding, dtype=str)
                df.columns = df.columns.astype(str).str.replace('\ufeff', '', regex=False).str.strip().str.upper()
                if not df.empty and len(df.columns) >= minimo_columnas:
                    return df, separador
            except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError):
                continue
    raise ValueError("CSV inválido. Utiliza ',' o ';' como separador y verifica que contenga las columnas requeridas.")

# ==========================================
# FUNCIONES DE VERIFICACIÓN DE ROLES (RBAC)
# ==========================================

def es_supervisor(user):
    return user.is_superuser or user.groups.filter(name='Supervisor').exists()

def es_usuario_autorizado(user):
    return user.is_superuser or user.groups.filter(name__in=['Supervisor', 'Usuario Autorizado']).exists()


# ==========================================
# PROCESAMIENTO CENTRALIZADO DEL FORMULARIO
# ==========================================

def procesar_accion_formulario(request, instance=None):
    """Maneja la lógica de los botones CALCULAR y GRABAR de forma centralizada."""
    accion = request.POST.get('accion')
    ingreso_por_montos = request.POST.get('ingreso_por_montos') == '1'
    nombres_factores = [f'factor_{i:02d}' for i in range(8, 38)]
    form = CalificacionForm(request.POST, instance=instance)
    
    if accion == 'calcular':
        montos = {}
        errores_calculo = []
        
        if not ingreso_por_montos:
            errores_calculo.append('Debes activar la opción "Ingreso por montos" para calcular.')
        else:
            for nombre in nombres_factores:
                valor = request.POST.get(nombre, '').strip()
                if valor == '':
                    montos[nombre] = Decimal('0')
                    continue
                try:
                    numero = Decimal(valor)
                    if not numero.is_finite() or numero < 0:
                        errores_calculo.append(f'{form.fields[nombre].label}: ingresa un número válido y positivo.')
                    else:
                        montos[nombre] = numero
                except InvalidOperation:
                    errores_calculo.append(f'{form.fields[nombre].label}: ingresa un número válido.')
        
        if not errores_calculo:
            total = sum(montos[f'factor_{i:02d}'] for i in range(8, 20))
            if total == 0:
                errores_calculo.append('La suma de los montos de los factores 08 al 19 debe ser mayor que cero.')
        
        if errores_calculo:
            for nombre in nombres_factores:
                form.errors.pop(nombre, None)
            form.add_error(None, 'No se pudo realizar el cálculo: ' + ' '.join(errores_calculo))
            return form, ingreso_por_montos, False
        else:
            datos_calculados = request.POST.copy()
            for nombre in nombres_factores:
                resultado = (montos[nombre] / total).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
                datos_calculados[nombre] = format(resultado, '.8f')
                
            form = CalificacionForm(datos_calculados, instance=instance)
            form.is_valid()
            return form, False, False # (form, ingreso_por_montos, is_ready_to_save)

    elif accion == 'grabar':
        if ingreso_por_montos:
            form.is_valid()
            for nombre in nombres_factores:
                form.errors.pop(nombre, None)
            form.add_error(None, 'Primero debes presionar CALCULAR para transformar los montos en factores.')
            return form, ingreso_por_montos, False
        
        return form, ingreso_por_montos, True

    return form, ingreso_por_montos, False


# ==========================================
# VISTAS PRINCIPALES (CRUD)
# ==========================================

@login_required
@user_passes_test(es_usuario_autorizado)
def lista_calificaciones(request):
    user_es_supervisor = es_supervisor(request.user)
    mostrar_modal = False
    ingreso_por_montos = False

    if request.method == 'POST':
        mostrar_modal = True
        form, ingreso_por_montos, is_ready = procesar_accion_formulario(request)
        if is_ready and form.is_valid():
            form.save()
            messages.success(request, 'Registro ingresado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm()

    calificaciones = CalificacionTributaria.objects.all().order_by('-id')
    
    # Filtros
    mercado = request.GET.get('mercado', '').strip()
    origen = request.GET.get('origen', '').strip()
    periodo_comercial = request.GET.get('periodo_comercial', '').strip()
    calificacion_pendiente = request.GET.get('calificacion_pendiente', '')
    
    periodos_disponibles = (
        CalificacionTributaria.objects.order_by()
        .values_list('periodo_comercial', flat=True)
        .distinct().order_by('-periodo_comercial')
    )

    # Aplicar Filtros
    if mercado:
        calificaciones = calificaciones.filter(mercado__icontains=mercado)
    if origen:
        calificaciones = calificaciones.filter(origen=origen)
    if periodo_comercial:
        calificaciones = calificaciones.filter(periodo_comercial=periodo_comercial)
    if calificacion_pendiente == '1':
        # Se considera pendiente si el monto es nulo o 0
        calificaciones = calificaciones.filter(Q(monto__isnull=True) | Q(monto=0))
        
    paginator = Paginator(calificaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    contexto = {
        'calificaciones': page_obj,
        'form': form,
        'es_supervisor': user_es_supervisor,
        'periodo_buscado': periodo_comercial,
        'origen_buscado': origen,
        'mercado_buscado': mercado,
        'calificacion_pendiente': calificacion_pendiente,
        'query_params': query_params.urlencode(),
        'mostrar_modal': mostrar_modal,
        'ingreso_por_montos': ingreso_por_montos,
        'periodos_disponibles': periodos_disponibles,
    }
    return render(request, 'mantenedor/lista.html', contexto)


@login_required
@user_passes_test(es_usuario_autorizado)
def editar_calificacion(request, pk):
    registro = get_object_or_404(CalificacionTributaria, pk=pk)
    user_es_supervisor = es_supervisor(request.user)
    mostrar_modal = True
    ingreso_por_montos = False
    
    if request.method == 'POST':
        form, ingreso_por_montos, is_ready = procesar_accion_formulario(request, instance=registro)
        if is_ready and form.is_valid():
            form.save()
            messages.success(request, 'Registro modificado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm(instance=registro)
        
    calificaciones = CalificacionTributaria.objects.all().order_by('-id')
    paginator = Paginator(calificaciones, 10)
    page_obj = paginator.get_page(1)
    periodos_disponibles = CalificacionTributaria.objects.order_by().values_list('periodo_comercial', flat=True).distinct().order_by('-periodo_comercial')
    
    return render(request, 'mantenedor/lista.html', {
        'calificaciones': page_obj,
        'form': form,
        'es_supervisor': user_es_supervisor,
        'abrir_modal_edicion': True,
        'mostrar_modal': mostrar_modal,
        'ingreso_por_montos': ingreso_por_montos,
        'periodos_disponibles': periodos_disponibles,
    })


@login_required
@user_passes_test(es_usuario_autorizado)
def copiar_calificacion(request, pk):
    registro_original = get_object_or_404(CalificacionTributaria, pk=pk)
    registro_original.pk = None
    user_es_supervisor = es_supervisor(request.user)
    mostrar_modal = True
    ingreso_por_montos = False
    
    if request.method == 'POST':
        form, ingreso_por_montos, is_ready = procesar_accion_formulario(request, instance=registro_original)
        if is_ready and form.is_valid():
            form.save()
            messages.success(request, 'Registro copiado exitosamente.')
            return redirect('lista_calificaciones')
    else:
        form = CalificacionForm(instance=registro_original)
        
    calificaciones = CalificacionTributaria.objects.all().order_by('-id')
    paginator = Paginator(calificaciones, 10)
    page_obj = paginator.get_page(1)
    periodos_disponibles = CalificacionTributaria.objects.order_by().values_list('periodo_comercial', flat=True).distinct().order_by('-periodo_comercial')
    
    return render(request, 'mantenedor/lista.html', {
        'calificaciones': page_obj,
        'form': form,
        'es_supervisor': user_es_supervisor,
        'abrir_modal_edicion': True,
        'mostrar_modal': mostrar_modal,
        'ingreso_por_montos': ingreso_por_montos,
        'periodos_disponibles': periodos_disponibles,
    })


# ==========================================
# VISTAS RESTRINGIDAS (SUPERVISOR)
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

    if request.method != 'POST':
        return redirect('lista_calificaciones')

    archivo = request.FILES.get('archivo_factor')
    
    if not archivo:
        messages.error(request, "No se recibió ningún archivo CSV.")
        return redirect('lista_calificaciones')

    try:
        df, separador = leer_csv_con_separador(archivo)
        df.columns = [str(col).replace('\ufeff', '').strip().lower() for col in df.columns]

        columnas_esperadas = ['mercado', 'periodo_comercial', 'ejercicio', 'instrumento', 'fecha_pago', 'descripcion', 'secuencia_evento', 'acogido_isfut', 'monto', 'factor_actualizacion']
        columnas_factores = [f'factor_{i:02d}' for i in range(8, 38)]
        columnas_esperadas.extend(columnas_factores)

        faltantes = [col for col in columnas_esperadas if col not in df.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas obligatorias: {', '.join(faltantes)}")

        if df.empty:
            raise ValueError("El archivo CSV no contiene registros.")

        df = df.fillna('')
        registros_a_crear = []
        errores = []

        for index, row in df.iterrows():
            numero_fila = index + 2
            try:
                mercado = obtener_texto_csv(row, 'mercado', numero_fila, 2)
                instrumento = obtener_texto_csv(row, 'instrumento', numero_fila, 40)
                ejercicio = obtener_texto_csv(row, 'ejercicio', numero_fila, 4)
                
                if not ejercicio.isdigit() or len(ejercicio) != 4:
                    raise ValueError("Ejercicio debe contener exactamente 4 dígitos.")

                descripcion = obtener_texto_csv(row, 'descripcion', numero_fila, 50)
                secuencia_evento = obtener_texto_csv(row, 'secuencia_evento', numero_fila, 10)
                
                if not secuencia_evento.isdigit():
                    raise ValueError("Secuencia evento debe contener solamente números.")

                periodo_comercial = convertir_entero_csv(row['periodo_comercial'], 'periodo_comercial')
                fecha_texto = obtener_texto_csv(row, 'fecha_pago', numero_fila, 10)
                
                try:
                    fecha_pago = datetime.strptime(fecha_texto, '%d-%m-%Y').date()
                except ValueError:
                    raise ValueError("Fecha de pago inválida. Formato esperado: DD-MM-AAAA.")

                acogido_isfut = convertir_isfut(row['acogido_isfut'])
                monto = convertir_decimal_csv(row['monto'], 'monto', decimales=2, max_digits=18)
                factor_actualizacion = convertir_decimal_csv(row['factor_actualizacion'], 'factor_actualizacion', decimales=8, max_digits=20, minimo=Decimal('0'), redondear=True)

                factores = {}
                for i in range(8, 38):
                    nombre = f'factor_{i:02d}'
                    valor = convertir_decimal_csv(row[nombre], nombre, decimales=8, max_digits=20, minimo=Decimal('0'), maximo=Decimal('1'), redondear=True)
                    factores[nombre] = valor

                nueva_calificacion = CalificacionTributaria(
                    mercado=mercado,
                    origen='CORREDOR',
                    periodo_comercial=periodo_comercial,
                    ejercicio=ejercicio,
                    instrumento=instrumento,
                    fecha_pago=fecha_pago,
                    descripcion=descripcion,
                    secuencia_evento=secuencia_evento,
                    acogido_isfut=acogido_isfut,
                    monto=monto,
                    factor_actualizacion=factor_actualizacion,
                    **factores
                )
                registros_a_crear.append(nueva_calificacion)

            except (ValueError, TypeError, InvalidOperation) as e:
                errores.append(f"Fila {numero_fila}: {str(e)}")

        if errores:
            detalle = '\n'.join(errores[:15])
            if len(errores) > 15:
                detalle += f"\nY {len(errores) - 15} errores adicionales."
            raise ValueError(f"Se encontraron {len(errores)} registros inválidos:\n{detalle}")
        
        with transaction.atomic():
            CalificacionTributaria.objects.bulk_create(registros_a_crear, batch_size=500)
        
        messages.success(request, f"Carga por factor exitosa. Se crearon {len(registros_a_crear)} registros.")

    except Exception as e:
        messages.error(request, f"Error al procesar el archivo CSV. Detalle: {str(e)}")

    return redirect('lista_calificaciones')


@login_required
def carga_monto(request):
    if not es_supervisor(request.user):
        raise PermissionDenied("Acceso denegado: Solo un Supervisor puede realizar cargas masivas.")
        
    if request.method == 'POST' and request.FILES.get('archivo_monto'):
        archivo = request.FILES['archivo_monto']
        try:
            df, separador = leer_csv_con_separador(archivo)
            df = df.fillna('')
            registros_a_crear = []
            errores = []

            for index, row in df.iterrows():
                numero_fila = index + 2
                try:
                    # 1. Mercado (Max 2 chars para cuadrar con el formulario)
                    mercado_val = str(row.get('MERCADO', '')).strip()[:2].upper()
                    if not mercado_val: 
                        mercado_val = 'AC'
                        
                    # 2. Fecha (Obligatoria para PostgreSQL)
                    raw_fecha = str(row.get('FEC_PAGO', '')).strip()
                    if not raw_fecha:
                        raise ValueError("La fecha de pago (FEC_PAGO) está vacía.")
                    try:
                        fecha_pago_val = datetime.strptime(raw_fecha, '%d-%m-%Y').date()
                    except ValueError:
                        raise ValueError(f"Fecha de pago inválida '{raw_fecha}'. Formato esperado: DD-MM-AAAA.")

                    # 3. Resto de campos de texto ajustados a la BD
                    instrumento_val = str(row.get('NEMOTECNICO', 'N/A')).strip()[:40]
                    ejercicio_val = str(row.get('EJERCICIO', '2025')).strip()[:4]
                    secuencia_evento_val = str(row.get('SEC_EVE', '')).strip()[:10]
                    descripcion_val = str(row.get('DESCRIPCION', '')).strip()[:50]

                    # 4. Calcular el Monto Base con Decimal exacto
                    suma_base = Decimal('0')
                    montos_dict = {}
                    
                    for i in range(8, 38):
                        col_name = f"MONTO_{i:02d}"
                        val_str = str(row.get(col_name, '0')).strip().replace('.', '').replace(',', '.')
                        if not val_str: val_str = '0'
                        
                        try:
                            monto_dec = Decimal(val_str)
                        except InvalidOperation:
                            monto_dec = Decimal('0')
                            
                        montos_dict[f"factor_{i:02d}"] = monto_dec
                        if 8 <= i <= 19:
                            suma_base += monto_dec

                    # 5. Calcular los 30 factores
                    factores_calculados = {}
                    for i in range(8, 38):
                        nombre_factor = f"factor_{i:02d}"
                        if suma_base > Decimal('0'):
                            factor_final = (montos_dict[nombre_factor] / suma_base).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
                        else:
                            factor_final = Decimal('0.00000000')
                        factores_calculados[nombre_factor] = factor_final

                    # 6. Construir el objeto
                    nueva_calificacion = CalificacionTributaria(
                        ejercicio=ejercicio_val,
                        mercado=mercado_val,
                        instrumento=instrumento_val,
                        fecha_pago=fecha_pago_val,
                        secuencia_evento=secuencia_evento_val,
                        descripcion=descripcion_val,
                        monto=suma_base.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        **factores_calculados
                    )
                    registros_a_crear.append(nueva_calificacion)

                except Exception as e:
                    errores.append(f"Fila {numero_fila}: {str(e)}")

            if errores:
                detalle = '\n'.join(errores[:10])
                if len(errores) > 10:
                    detalle += f"\nY {len(errores) - 10} errores adicionales."
                raise ValueError(f"Se encontraron registros inválidos:\n{detalle}")

            # Guardado atómico para prevenir registros incompletos
            with transaction.atomic():
                CalificacionTributaria.objects.bulk_create(registros_a_crear, batch_size=500)
                
            messages.success(request, f'¡Carga exitosa! Se procesaron y calcularon {len(registros_a_crear)} registros correctamente.')

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo CSV. Detalle: {str(e)}")

        return redirect('lista_calificaciones')
        
    return redirect('lista_calificaciones')