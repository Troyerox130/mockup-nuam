from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
import pandas as pd
from mantenedor.models import CalificacionTributaria
from mantenedor.forms import CalificacionForm, CargaFactorForm, CargaMontoForm
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from django.db import transaction
from mantenedor.models import CalificacionTributaria


def obtener_texto_csv(row, campo, fila, max_length=None):
    """Obtiene un campo obligatorio y verifica su longitud."""

    valor = row.get(campo, '')

    if pd.isna(valor):
        valor = ''

    valor = str(valor).strip()

    if not valor:
        raise ValueError(f"El campo '{campo}' está vacío.")

    if max_length and len(valor) > max_length:
        raise ValueError(
            f"El campo '{campo}' supera el máximo de "
            f"{max_length} caracteres. Recibido: {len(valor)}."
        )

    return valor


def convertir_isfut(valor):
    """Convierte S/SI y N/NO a valores booleanos."""

    valor = str(valor).strip().upper()

    equivalencias = {
        'S': True,
        'SI': True,
        'N': False,
        'NO': False
    }

    if valor not in equivalencias:
        raise ValueError(
            f"Valor inválido para acogido_isfut: '{valor}'. "
            "Utiliza S, SI, N o NO."
        )

    return equivalencias[valor]


def convertir_entero_csv(valor, campo, max_length=None):
    """Valida y convierte un valor numérico entero."""

    valor = str(valor).strip()

    if not valor.isdigit():
        raise ValueError(
            f"El campo '{campo}' debe contener un número entero."
        )

    if max_length and len(valor) > max_length:
        raise ValueError(
            f"El campo '{campo}' supera el máximo de "
            f"{max_length} dígitos."
        )

    return int(valor)


def convertir_decimal_csv(
    valor,
    campo,
    decimales,
    max_digits,
    minimo=None,
    maximo=None,
    redondear=False
):
    """Valida y convierte valores decimales utilizando Decimal."""

    valor = str(valor).strip()

    if not valor:
        raise ValueError(f"El campo '{campo}' está vacío.")

    # Aceptar coma decimal cuando no existe punto decimal.
    if ',' in valor and '.' not in valor and valor.count(',') == 1:
        valor = valor.replace(',', '.')

    try:
        numero = Decimal(valor)
    except InvalidOperation:
        raise ValueError(
            f"El campo '{campo}' contiene un valor decimal inválido: '{valor}'."
        )

    if not numero.is_finite():
        raise ValueError(f"El campo '{campo}' debe ser un número finito.")

    # Comprobar los límites antes de redondear.
    if minimo is not None and numero < minimo:
        raise ValueError(f"El campo '{campo}' no puede ser negativo.")

    if maximo is not None and numero > maximo:
        raise ValueError(f"El campo '{campo}' no puede superar {maximo}.")

    # Comprobar o redondear los decimales.
    precision = Decimal('1').scaleb(-decimales)

    if redondear:
        numero = numero.quantize(precision, rounding=ROUND_HALF_UP)
    elif numero.as_tuple().exponent < -decimales:
        raise ValueError(
            f"El campo '{campo}' permite máximo {decimales} decimales."
        )

    # Validar precisión máxima del DecimalField.
    digitos = len(numero.as_tuple().digits)
    exponente = numero.as_tuple().exponent
    digitos_enteros = max(digitos + exponente, 0)

    if digitos_enteros > max_digits - decimales:
        raise ValueError(
            f"El campo '{campo}' supera la precisión máxima permitida."
        )

    return numero

def leer_csv_con_separador(archivo, minimo_columnas=6):
    """
    Lee un CSV probando exclusivamente los separadores ';' y ','.
    Devuelve el DataFrame y el separador detectado.
    """

    separadores = [';', ',']
    encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']

    for separador in separadores:
        for encoding in encodings:
            try:
                archivo.seek(0)

                df = pd.read_csv(
                    archivo,
                    sep=separador,
                    encoding=encoding,
                    dtype=str
                )
                df.columns = (
                    df.columns
                    .astype(str)
                    .str.replace('\ufeff', '', regex=False)
                    .str.strip()
                    .str.upper()
                )

                df.columns = df.columns.str.strip()

                # Comprobar que la estructura sea válida
                if not df.empty and len(df.columns) >= minimo_columnas:
                    return df, separador

            except (
                UnicodeDecodeError,
                pd.errors.ParserError,
                pd.errors.EmptyDataError,
                ValueError
            ):
                continue

    raise ValueError(
        "CSV inválido. Utiliza ',' o ';' como separador "
        "y verifica que contenga las columnas requeridas."
    )

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
    
    mostrar_modal = False
    ingreso_por_montos = False

    if request.method == 'POST':
        accion = request.POST.get('accion')
        ingreso_por_montos = request.POST.get('ingreso_por_montos') == '1'
        mostrar_modal = True

        nombres_factores = [
            f'factor_{i:02d}' for i in range(8, 38)
        ]

        if accion == 'calcular':

            form = CalificacionForm(request.POST)
            form.is_valid()

            montos = {}
            errores_calculo = []

            # Validar y obtener los montos ingresados
            if not ingreso_por_montos:
                errores_calculo.append(
                    'Debes activar la opción "Ingreso por montos" para calcular.'
                )
            else:
                for nombre in nombres_factores:
                    valor = request.POST.get(nombre, '').strip()

                    # Los campos vacíos se consideran cero
                    if valor == '':
                        montos[nombre] = Decimal('0')
                        continue

                    try:
                        numero = Decimal(valor)

                        if not numero.is_finite():
                            errores_calculo.append(
                                f'{form.fields[nombre].label}: ingresa un número válido.'
                            )
                        elif numero < 0:
                            errores_calculo.append(
                                f'{form.fields[nombre].label}: no puede ser negativo.'
                            )
                        else:
                            montos[nombre] = numero

                    except InvalidOperation:
                        errores_calculo.append(
                            f'{form.fields[nombre].label}: ingresa un número válido.'
                        )

            # Calcular el denominador utilizando solamente los factores 08 al 19
            if not errores_calculo:
                total = sum(
                    montos[f'factor_{i:02d}']
                    for i in range(8, 20)
                )

                if total == 0:
                    errores_calculo.append(
                        'La suma de los montos de los factores 08 al 19 debe ser mayor que cero.'
                    )

            # Si hay errores, conservar los valores ingresados
            if errores_calculo:

                # Los límites normales de los factores no corresponden
                # mientras estamos interpretando los campos como montos.
                for nombre in nombres_factores:
                    form.errors.pop(nombre, None)

                form.add_error(
                    None,
                    'No se pudo realizar el cálculo: ' + ' '.join(errores_calculo)
                )

            else:
                # Reemplazar los montos por sus factores calculados
                datos_calculados = request.POST.copy()

                for nombre in nombres_factores:
                    resultado = (
                        montos[nombre] / total
                    ).quantize(
                        Decimal('0.00000001'),
                        rounding=ROUND_HALF_UP
                    )

                    datos_calculados[nombre] = format(resultado, '.8f')

                # Crear el formulario con los factores resultantes
                form = CalificacionForm(datos_calculados)
                form.is_valid()

                # Desactivar el modo de ingreso por montos
                ingreso_por_montos = False

        elif accion == 'grabar':

            form = CalificacionForm(request.POST)

            # Evitar que se guarden montos como si fueran factores
            if ingreso_por_montos:

                form.is_valid()

                for nombre in nombres_factores:
                    form.errors.pop(nombre, None)

                form.add_error(
                    None,
                    'Primero debes presionar CALCULAR para transformar los montos en factores.'
                )

            elif form.is_valid():
                form.save()
                messages.success(
                    request,
                    'Registro ingresado exitosamente.'
                )
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
        'mostrar_modal': mostrar_modal,
        'ingreso_por_montos': ingreso_por_montos,
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
    print(CalificacionTributaria._meta.db_table)
    print(CalificacionTributaria.objects.count())   
    
    print("1. Entrando a carga_factor")
    print("2. Método:", request.method)

    # Comprobar permisos
    if not es_supervisor(request.user):
        raise PermissionDenied("Acceso denegado.")

    # Comprobar que sea una solicitud POST
    if request.method != 'POST':
        return redirect('lista_calificaciones')

    # Obtener archivo
    archivo = request.FILES.get('archivo_factor')
    
    print("3. Archivo recibido:", archivo)

    if not archivo:
        messages.error(request, "No se recibió ningún archivo CSV.")
        return redirect('lista_calificaciones')

    try:

        # 1. Leer CSV y detectar separador
        df, separador = leer_csv_con_separador(archivo)
        
        print("4. CSV leído correctamente")
        print("5. Separador:", separador)
        print("6. Dimensiones:", df.shape)

        # Normalizar encabezados
        df.columns = [
            str(col).replace('\ufeff', '').strip().lower()
            for col in df.columns
        ]

        # 2. Definir encabezados esperados
        columnas_esperadas = [
            'mercado',
            'periodo_comercial',
            'ejercicio',
            'instrumento',
            'fecha_pago',
            'descripcion',
            'secuencia_evento',
            'acogido_isfut',
            'monto',
            'factor_actualizacion'
        ]

        columnas_factores = [
            f'factor_{i:02d}'
            for i in range(8, 38)
        ]

        columnas_esperadas.extend(columnas_factores)

        # 3. Validar estructura del CSV
        faltantes = [
            col for col in columnas_esperadas
            if col not in df.columns
        ]

        adicionales = [
            col for col in df.columns
            if col not in columnas_esperadas
        ]

        if faltantes:
            raise ValueError(
                f"Faltan columnas obligatorias: {', '.join(faltantes)}"
            )

        if adicionales:
            raise ValueError(
                f"Columnas no reconocidas: {', '.join(adicionales)}"
            )

        if df.empty:
            raise ValueError("El archivo CSV no contiene registros.")

        # No reemplazar vacíos por cero: deben validarse.
        df = df.fillna('')

        registros_a_crear = []
        errores = []

        # 4. Procesar cada registro
        for index, row in df.iterrows():

            numero_fila = index + 2

            try:

                # Campos de texto
                mercado = obtener_texto_csv(
                    row, 'mercado', numero_fila, 2
                )

                instrumento = obtener_texto_csv(
                    row, 'instrumento', numero_fila, 40
                )

                ejercicio = obtener_texto_csv(
                    row, 'ejercicio', numero_fila, 4
                )

                if not ejercicio.isdigit() or len(ejercicio) != 4:
                    raise ValueError(
                        "Ejercicio debe contener exactamente 4 dígitos."
                    )

                descripcion = obtener_texto_csv(
                    row, 'descripcion', numero_fila, 50
                )

                secuencia_evento = obtener_texto_csv(
                    row, 'secuencia_evento', numero_fila, 10
                )

                if not secuencia_evento.isdigit():
                    raise ValueError(
                        "Secuencia evento debe contener solamente números."
                    )

                # Periodo comercial
                periodo_comercial = convertir_entero_csv(
                    row['periodo_comercial'],
                    'periodo_comercial'
                )

                # Fecha de pago
                fecha_texto = obtener_texto_csv(
                    row, 'fecha_pago', numero_fila, 10
                )

                try:
                    fecha_pago = datetime.strptime(
                        fecha_texto, '%d-%m-%Y'
                    ).date()
                except ValueError:
                    raise ValueError(
                        "Fecha de pago inválida. Formato esperado: DD-MM-AAAA."
                    )

                # ISFUT
                acogido_isfut = convertir_isfut(
                    row['acogido_isfut']
                )

                # Monto: DecimalField(max_digits=18, decimal_places=2)
                monto = convertir_decimal_csv(
                    row['monto'],
                    'monto',
                    decimales=2,
                    max_digits=18
                )

                # Factor de actualización: DecimalField(20,8)
                factor_actualizacion = convertir_decimal_csv(
                    row['factor_actualizacion'],
                    'factor_actualizacion',
                    decimales=8,
                    max_digits=20,
                    minimo=Decimal('0'),
                    redondear=True
                )

                # Factores 08 hasta 37
                factores = {}

                for i in range(8, 38):

                    nombre = f'factor_{i:02d}'

                    valor = convertir_decimal_csv(
                        row[nombre],
                        nombre,
                        decimales=8,
                        max_digits=20,
                        minimo=Decimal('0'),
                        maximo=Decimal('1'),
                        redondear=True
                    )

                    factores[nombre] = valor

                # 5. Crear objeto sin guardarlo todavía
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

                errores.append(
                    f"Fila {numero_fila}: {str(e)}"
                )

        # 6. Si existen errores, no guardar ningún registro
        if errores:

            detalle = '\n'.join(errores[:15])

            if len(errores) > 15:
                detalle += (
                    f"\nY {len(errores) - 15} errores adicionales."
                )

            raise ValueError(
                f"Se encontraron {len(errores)} registros inválidos:\n"
                f"{detalle}"
            )
        
        print("7. Registros preparados:", len(registros_a_crear))

        # 7. Guardar todos los registros en una transacción
        with transaction.atomic():

            CalificacionTributaria.objects.bulk_create(
                registros_a_crear,
                batch_size=500
            )
        
        print("8. Registros guardados correctamente")
        messages.success(
            request,
            f"Carga por factor exitosa. "
            f"Se crearon {len(registros_a_crear)} registros."
        )

    except Exception as e:

        messages.error(
            request,
            f"Error al procesar el archivo CSV. Detalle: {str(e)}"
        )

    return redirect('lista_calificaciones')

@login_required
def carga_monto(request):
    """Procesa el archivo CSV para Carga x Monto con formato exacto, calcula proporciones y guarda masivamente"""
    if not es_supervisor(request.user):
        raise PermissionDenied("Acceso denegado: Solo un Supervisor puede realizar cargas masivas.")
        
    if request.method == 'POST' and request.FILES.get('archivo_monto'):
        archivo = request.FILES['archivo_monto']
        try:
            df, separador = leer_csv_con_separador(archivo)
            
            
                
            df = df.fillna(0)
            registros_a_crear = []
            
            for index, row in df.iterrows():
                print(row['MERCADO'])

            for index, row in df.iterrows():
                # 1. Calcular el "Monto Base" (Suma exacta de las columnas Monto_08 a la Monto_19)
                suma_base = 0.0
                for i in range(8, 20):
                    col_name = f"MONTO_{i:02d}"
                    if col_name in df.columns:
                        val_str = str(row[col_name]).strip().replace('.', '').replace(',', '.')
                        try:
                            suma_base += float(val_str) if val_str else 0.0
                        except ValueError:
                            pass

                # 2. Calcular los 30 factores (F-08 hasta F-37) redondeados a 8 decimales
                factores_calculados = {}
                for i in range(8, 38):
                    col_name = f"MONTO_{i:02d}"
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