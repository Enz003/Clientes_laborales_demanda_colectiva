from docxtpl import DocxTemplate, InlineImage
import uuid
from PIL import Image
from docx.shared import Mm,Cm
import requests
from io import BytesIO
from datetime import datetime
import qrcode
import os
import sys
import shutil
import time


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        #PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def formatear_fecha_conInput(dia,mes,anho):
    
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    
    return f"{dia} de {meses[int(mes)-1]} de {anho}"

def obtener_fecha_formateada():
    # Diccionario de meses en español
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    
    # Obtener fecha actual
    hoy = datetime.now()
    dia = hoy.day
    mes_num = hoy.month
    año = hoy.year
    
    # Formatear la fecha
    fecha_formateada = f"{dia} días del mes de {meses[mes_num]} del año {año}"
    
    return fecha_formateada




def limpiar_carpeta(ruta_carpeta, eliminar_subcarpetas=False):
    """
    Elimina todos los archivos de una carpeta local, con opción para eliminar subcarpetas.
    
    Args:
        ruta_carpeta (str): Ruta absoluta o relativa de la carpeta a limpiar
        eliminar_subcarpetas (bool): Si es True, también elimina subcarpetas y su contenido
    
    Returns:
        tuple: (archivos_eliminados, errores)
    """
    archivos_eliminados = 0
    errores = 0
    
    try:
        # Verificar si la carpeta existe
        ruta_carpeta = resource_path(ruta_carpeta)
        if not os.path.exists(ruta_carpeta):
            raise FileNotFoundError(f"La carpeta no existe: {ruta_carpeta}")
        
        # Recorrer todos los elementos en la carpeta
        for nombre in os.listdir(ruta_carpeta):
            ruta_completa = os.path.join(ruta_carpeta, nombre)
            
            try:
                if os.path.isfile(ruta_completa):
                    os.remove(ruta_completa)
                    archivos_eliminados += 1
                elif os.path.isdir(ruta_completa) and eliminar_subcarpetas:
                    shutil.rmtree(ruta_completa)
                    archivos_eliminados += 1  # Contamos la carpeta como un elemento eliminado
            except Exception as e:
                print(f"Error al eliminar {ruta_completa}: {str(e)}")
                errores += 1
        
        return (archivos_eliminados, errores)
    
    except Exception as e:
        print(f"Error general: {str(e)}")
        return (0, 1)

def generar_qr_inline(doc, enlace, ancho_mm=30):
    """
    Genera un código QR desde un enlace y lo devuelve como InlineImage para docxtpl.
    
    Parámetros:
        doc: instancia de DocxTemplate
        enlace: texto o URL a codificar en el QR
        ancho_mm: ancho del QR en milímetros (default: 30)
    
    Retorna:
        InlineImage listo para usarse en el contexto del template
    """
    # Crear imagen QR
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(enlace)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar QR como imagen temporal
    nombre_archivo = f"Img/qr_{uuid.uuid4().hex}.png"
    nombre_archivo = resource_path(nombre_archivo)
    img.save(nombre_archivo)

    # Crear InlineImage
    return InlineImage(doc, nombre_archivo, width=Mm(ancho_mm))

# Extrae el ID de la URL de Google Drive (si está en formato "open?id=")
def convertir_url_google_drive(url):
    if "open?id=" in url:
        id_imagen = url.split("open?id=")[-1]
        return f"https://drive.google.com/uc?export=download&id={id_imagen}"
    return url  # Ya es directa


def generar_imagen_inline(doc, url, ancho_cm=14):


    nombre_archivo = f"Img/imagen_{uuid.uuid4().hex}.jpg"
    nombre_archivo = resource_path(nombre_archivo)

    url_valida = convertir_url_google_drive(url)
    response = requests.get(url_valida)

    content_type = response.headers.get('Content-Type', '')
    if 'image' not in content_type:
        raise Exception(f"La URL no contiene una imagen válida. Content-Type: {content_type}")

    try:
        img = Image.open(BytesIO(response.content))
        img.verify()
        img = Image.open(BytesIO(response.content))
    except Exception as e:
        raise Exception("El contenido descargado no es una imagen válida") from e

    os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)

    # 🔧 Solución al error RGBA
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    img.save(nombre_archivo)

    width_px, height_px = img.size
    dpi = img.info.get("dpi", (96, 96))[0]
    ancho_in = ancho_cm / 2.54
    escala = (ancho_in * dpi) / width_px
    alto_cm = (height_px * escala) / dpi * 2.54

    return InlineImage(doc, nombre_archivo, width=Cm(ancho_cm), height=Cm(alto_cm))




def  FORM_DATOS_NUEVOS_PARA_TRABAJADOR(cliente):
    contexto = {
        'nombre_completo': cliente['Nombres y Apellidos completos como esta en tu Cedula.'],
        'estado_civil': cliente['Estado Civil como esta en tu cedula'],
        'nacionalidad': cliente['Nacionalidad'],
        'ci': cliente['Numero de Cedula'],
        'ciudad': cliente['Ciudad'],
        'barrio': cliente['Barrio'],
        'direccion_calle': cliente['Direccion Particular, Calles, Numero de casa'],
        'telefono': cliente['Telefono de contacto personal'],
        'empresa_que_trabajo': cliente['Empresa en la que trabajo <Razon Social>'],
        'direccion_empresa': cliente['Direccion de la Empresa'],
        'ruc_empresa':cliente['Ruc de la empresa'],
        'fecha_ingreso': cliente['Fecha de ingreso'],
        'fecha_despido': cliente['Fecha de Despido'],
        'jornada_laboral': cliente['JORNADA LABORAL. Como es o era tu Jornada Laboral? Lunes a Viernes, Lunes a Lunes?'],
        'horario_laboral': cliente['HORARIO DE TRABAJO. Como era tu Horario que Cumplias? Ej 8.00 a 18.00'],
        'salario': cliente['CUANTO ERA SALARIO. Mensual, semanal, diario?'],
        'ips': cliente['IPS'],
        'bonificacion_familiar':cliente['Bonficacion familiar por Cuantos hijos si la respuesta fue SI'],
        'tarea_realizada': cliente['Describe las tareas o funciones que desempenabas en el lugar de trabajo.'],
        'motivo_despido': cliente['MOTIVO DE DESPIDO. Cuentanos como se dio la situacion.'],
        'quien_lo_despidio': cliente['Quien te Comunico de tu despido?. Nombre Apellido, cargo en la empresa.'],
        'medio_del_despido': cliente['DESPIDO COMUNICACION. Como te comunicaron tu despido. Verbal, por escrito con nota, por llamada telefonica, por mensaje de texto?'],
        'salarios_pendientes': cliente['SALARIOS PENDIENTES. Te deben Salarios, Cuanto de cuantos dias o meses?'],
        'medio_pago_salario': cliente['PAGOS DE SALARIOS. Como recibias los pagos de salario o jornales?. Efectivo, Trasferencia, giros? via que banco?'],
        'vacaciones_pendientes': cliente['VACACIONES. Salias o tenias vacaciones? Te deben vacaciones?'],
        'aguinaldo_pendiente': cliente['AGUINALDO. Recibias Aguinaldo?. Te pagaban o te debe?'],
        'contaba_contrato': cliente['CONTRATO DE TRABAJO. Tenias contrato de Trabajo Firmado'],
        'ofrecio_liquidacion': cliente['LIQUIDACION.Te presentaron tu liquidacion de salarios y haberes al momento del despido?. Adjuntar Foto.'],
        'firmo_documento_en_blanco': cliente['Firmaste en algun momento algun Documento en blanco o pagare?'],
        'observaciones': cliente['Alguna informacion adicional que deseas agregar?'],
        'entrevistador':cliente['Entrevista realizada por']
    }

    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    ruta_abrir = resource_path('Plantilla/Plantillla_Formulario_Datos.docx')
    doc = DocxTemplate(ruta_abrir)
    time.sleep(5)

    imagen_actor = generar_imagen_inline(doc, cliente['Adjunta Imagen de la Ubicacion de Google Maps de casa Trabajador.'])
    link_ubicacion_actor = cliente['Ubicacion de tu casa. Copia el link de la ubicacion de google maps']
    qr_actor = generar_qr_inline(doc,link_ubicacion_actor)
    imagen_demandado = generar_imagen_inline(doc,cliente['Adjunta Imagen de la Ubicacion de Google Maps de la empresa'])
    link_ubicacion_demandado = cliente['Ubicacion de la empresa']
    qr_demandado = generar_qr_inline(doc,link_ubicacion_demandado)
    imagenesYfecha = {'fecha_hoy': fecha_actual,
                    'imagen_actor':imagen_actor,
                    'link_ubicacion_actor': link_ubicacion_actor,
                    'imagen_demandado':imagen_demandado,
                    'link_ubicacion_demandado':link_ubicacion_demandado,
                    'qr_actor':qr_actor,
                    'qr_demandado':qr_demandado}
    contexto.update(imagenesYfecha)


    doc.render(contexto)

    carpeta_limpiar = resource_path('Img')
    limpiar_carpeta(carpeta_limpiar)

    ruta_guardar = resource_path(f'Generado/Formulario_Datos_{contexto['ci']}.docx') 
    doc.save(ruta_guardar)

def  Carta_Poder(cliente):
    contexto = {
        'fecha': obtener_fecha_formateada(),
        'nombre_completo': cliente['Nombres y Apellidos completos como esta en tu Cedula.'].upper(),
        'estado_civil': cliente['Estado Civil como esta en tu cedula'].lower(),
        'nacionalidad': cliente['Nacionalidad'].lower(),
        'ci': cliente['Numero de Cedula'],
        'ciudad': cliente['Ciudad'].capitalize(),
        'direccion_calle': cliente['Direccion Particular, Calles, Numero de casa'],
        'empresa_que_trabajo': cliente['Empresa en la que trabajo <Razon Social>'].upper(),
        'direccion_empresa': cliente['Direccion de la Empresa'],
        'ciudad_empresa': cliente['Ciudad de la empresa'].capitalize(),
        'ruc_empresa':cliente['Ruc de la empresa'] 
    }

    if cliente['Sexo']=='Femenino':
        contexto['estado_civil']=contexto['estado_civil'][:-1]+'a'

    ruta_abrir = resource_path('Plantilla/Carta_de_Poder.docx')
    doc = DocxTemplate(ruta_abrir)



    doc.render(contexto)

    ruta_guardar = resource_path(f'Generado/Carta_de_Poder_{contexto['ci']}.docx')
    doc.save(ruta_guardar)

def Carta_Compromiso(cliente):
   
    contexto = {
        'nombre_completo': cliente['Nombres y Apellidos completos como esta en tu Cedula.'].upper(),
        'fecha': obtener_fecha_formateada(),
        'ci': cliente['Numero de Cedula'],
        'ciudad': cliente['Ciudad'].capitalize(),
        'direccion_calle': cliente['Direccion Particular, Calles, Numero de casa'],
        'empresa_que_trabajo': cliente['Empresa en la que trabajo <Razon Social>'].upper(),
        'ruc_empresa':cliente['Ruc de la empresa']
    }

    ruta_abrir = resource_path('Plantilla/Carta_Compromiso.docx')
    doc = DocxTemplate(ruta_abrir)

    doc.render(contexto)

    ruta_guardar = resource_path(f'Generado/Carta_Compromiso_{contexto['ci']}.docx') 
    doc.save(ruta_guardar)
    
def Desistimiento_de_renuncia(cliente):
    contexto = {
        'nombre_completo': cliente['Nombres y Apellidos completos como esta en tu Cedula.'].upper(),
        'ci': cliente['Numero de Cedula']
    }

    ruta_abrir = resource_path('Plantilla/Desistimiento_de_Renuncia.docx')
    doc = DocxTemplate(ruta_abrir)

    doc.render(contexto)

    ruta_cerrar = resource_path(f'Generado/Desistimiento_de_renuncia_{contexto['ci']}.docx')
    doc.save(ruta_cerrar)

def Nota_de_Renuncia(cliente):
    contexto = {
        'nombre_completo': cliente['Nombres y Apellidos completos como esta en tu Cedula.'].upper(),
        'ci': cliente['Numero de Cedula'],
        'empresa_que_trabajo': cliente['Empresa en la que trabajo <Razon Social>'].upper(),
        'ruc_empresa':cliente['Ruc de la empresa']
    }

    ruta_abrir = resource_path('Plantilla/Nota_de_Renuncia.docx')
    doc = DocxTemplate(ruta_abrir)

    doc.render(contexto)

    ruta_cerrar = resource_path(f'Generado/Nota_de_Renuncia_{contexto['ci']}.docx')
    doc.save(ruta_cerrar)
    
def documento_demanda(cliente):
    ruta_abrir = resource_path('Plantilla/documento_demanda.docx')
    doc = DocxTemplate(ruta_abrir)
    
    contexto = {
        'nombre_completo': cliente['Nombres y Apellidos completos como esta en tu Cedula.'].upper(),
        'estado_civil': cliente['Estado Civil como esta en tu cedula'].lower(),
        'nacionalidad': cliente['Nacionalidad'].lower(),
        'ci': cliente['Numero de Cedula'],
        'ciudad': cliente['Ciudad'].lower(),
        'barrio': cliente['Barrio'].lower(),
        'direccion_calle': cliente['Direccion Particular, Calles, Numero de casa'],
        'telefono': cliente['Telefono de contacto personal'],
        'empresa_que_trabajo': cliente['Empresa en la que trabajo <Razon Social>'].upper(),
        'direccion_empresa': cliente['Direccion de la Empresa'],
        'ciudad_empresa': cliente['Ciudad de la empresa'],
        'ruc_empresa':cliente['Ruc de la empresa'],
        'fecha_ingreso': cliente['Fecha de ingreso'],
        'jornada_laboral': cliente['JORNADA LABORAL. Como es o era tu Jornada Laboral? Lunes a Viernes, Lunes a Lunes?'],
        'horario_laboral': cliente['HORARIO DE TRABAJO. Como era tu Horario que Cumplias? Ej 8.00 a 18.00'],
        'salario': cliente['CUANTO ERA SALARIO. Mensual, semanal, diario?'],
        'ips': cliente['IPS'],
        'bonificacion_familiar':cliente['Bonficacion familiar por Cuantos hijos si la respuesta fue SI'],
        'tarea_realizada': cliente['Describe las tareas o funciones que desempenabas en el lugar de trabajo.'].lower(),
        'motivo_despido': cliente['MOTIVO DE DESPIDO. Cuentanos como se dio la situacion.'],
        'quien_lo_despidio': cliente['Quien te Comunico de tu despido?. Nombre Apellido, cargo en la empresa.'],
        'medio_del_despido': cliente['DESPIDO COMUNICACION. Como te comunicaron tu despido. Verbal, por escrito con nota, por llamada telefonica, por mensaje de texto?'],
        'salarios_pendientes': cliente['SALARIOS PENDIENTES. Te deben Salarios, Cuanto de cuantos dias o meses?'],
        'medio_pago_salario': cliente['PAGOS DE SALARIOS. Como recibias los pagos de salario o jornales?. Efectivo, Trasferencia, giros? via que banco?'],
        'vacaciones_pendientes': cliente['VACACIONES. Salias o tenias vacaciones? Te deben vacaciones?'],
        'aguinaldo_pendiente': cliente['AGUINALDO. Recibias Aguinaldo?. Te pagaban o te debe?'],
        'contaba_contrato': cliente['CONTRATO DE TRABAJO. Tenias contrato de Trabajo Firmado'],
        'ofrecio_liquidacion': cliente['LIQUIDACION.Te presentaron tu liquidacion de salarios y haberes al momento del despido?. Adjuntar Foto.'],
        'firmo_documento_en_blanco': cliente['Firmaste en algun momento algun Documento en blanco o pagare?'],
        'observaciones': cliente['Alguna informacion adicional que deseas agregar?'],
        'entrevistador':cliente['Entrevista realizada por'],
        'prefijo': 'el Sr' if cliente['Sexo']=='Masculilno' else 'la Sra'
    }

    

    fecha_ingreso = str(cliente['Fecha de ingreso']).split('/')
    dia_ingreso = fecha_ingreso[0]
    mes_ingreso = fecha_ingreso[1]
    anho_ingreso = fecha_ingreso[2]

    if cliente['Sexo']=='Femenino':
        contexto['estado_civil']=contexto['estado_civil'][:-1]+'a'

    contexto.update({   
                     'fecha_ingreso':formatear_fecha_conInput(dia_ingreso,mes_ingreso,anho_ingreso),
                     'anho_ingreso':anho_ingreso})
    doc.render(contexto)

    ruta_cerrar = resource_path(f'Generado/Demanda {cliente['Nombres y Apellidos completos como esta en tu Cedula.'].split()[0]} contra {cliente['Empresa en la que trabajo <Razon Social>']}.docx')
    doc.save(ruta_cerrar)
    