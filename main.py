import traceback
import time
import flet as ft
from flet import *

from funciones_de_API import get_authenticated_service, get_client_by_cedula, process_client_data,subir_archivos_a_drive,SPREADSHEET_ID,PARENT_FOLDER_ID,SHEET_NAME
from crear_documentos import limpiar_carpeta, FORM_DATOS_NUEVOS_PARA_TRABAJADOR,Carta_Poder,Carta_Compromiso,Desistimiento_de_renuncia,Nota_de_Renuncia,documento_demanda,resource_path


class DemandaLaboralApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.verification_state = False
        self.setup_page()
        self.create_controls()
        self.setup_events()
        self.create_view()
        # Variables de la autenticacion
        self.sheets_service = get_authenticated_service('sheets', 'v4')
        self.drive_service = get_authenticated_service('drive', 'v3')
        # Variables constantes referentes a las ID y direcciones de los recursos de Drive
        self.SPREADSHEET_ID = SPREADSHEET_ID
        self.SHEET_NAME = SHEET_NAME 
        self.PARENT_FOLDER_ID = PARENT_FOLDER_ID
        # Diccionario con datos del cliente
        self.cliente = {}

    def setup_page(self):
        """Configura las propiedades iniciales de la página"""
        self.page.title = "Clientes Demanda Laboral colectiv: ANDE"
        self.page.window_width = 650
        self.page.window_height = 750
        self.page.window_resizable = False
        self.page.padding = 30
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.GREY_100

    def create_controls(self):
        """Crea todos los controles de la interfaz"""
        # Logo
        ruta_logo = resource_path('Logo/logobernis.png')
        self.logo = ft.Container(
            content=ft.Image(
                src=ruta_logo,
                width=300,
                height=300,
                opacity=0.1,
                fit=ft.ImageFit.CONTAIN
            ),
            alignment=ft.alignment.center,
        )
        
        # Campo de cédula
        self.cedula_field = ft.TextField(
            label="Número de Cédula",
            hint_text="Ingrese número de cédula del cliente",
            border_radius=15,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_700,
            width=450,
            height=60,
            text_size=16,
            content_padding=15,
            prefix_icon=ft.Icons.BADGE_OUTLINED,
        )
        
        # Botones
        self.verify_button = ft.ElevatedButton(
            text="Verificar Cédula",
            icon=ft.Icons.VERIFIED_OUTLINED,
            width=200,
            height=50,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=10,
            ),
        )
        
        self.reset_button = ft.ElevatedButton(
            text="Nueva Consulta",
            icon=ft.Icons.REFRESH_OUTLINED,
            width=200,
            height=50,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=10,
            ),
        )
        
        self.generate_button = ft.ElevatedButton(
            text="Generar Documentos",
            icon=ft.Icons.DESCRIPTION_OUTLINED,
            width=200,
            height=50,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.DEEP_PURPLE_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=10,
            ),
        )
        
        # Mensaje de estado
        self.status_message = ft.Markdown(
            "",
            selectable=True,
            on_tap_link=lambda e: self.page.launch_url(e.data),
        )

    def setup_events(self):
        """Configura los eventos de los controles"""
        self.verify_button.on_click = self.toggle_verification
        self.reset_button.on_click = self.toggle_verification
        self.generate_button.on_click = self.generate_documents

    def create_view(self):
        """Crea la vista principal de la aplicación"""
        content = ft.Stack(
            [
                self.logo,
                ft.Column(
                    [
                        ft.Container(height=20),
                        ft.Text(
                            "PROCESO LABORAL INDIVIDUAL",
                            size=26,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_900,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=40),
                        self.cedula_field,
                        ft.Container(height=30),
                        ft.Row(
                            [self.verify_button, self.reset_button, self.generate_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=15,
                            wrap=True,
                        ),
                        ft.Container(height=30),
                        self.status_message,
                        ft.Container(height=20),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                )
            ]
        )
        self.page.add(content)
        

    def show_loading(self, message="Buscando Cliente..."):
        """Muestra un indicador de carga"""
        self.status_message.value = f"⏳ {message}"
        # Deshabilitar botones durante la carga
        self.verify_button.disabled = True
        self.reset_button.disabled = True
        self.generate_button.disabled = True
        self.page.update()

    def toggle_verification(self, e):
        """Alterna entre estados de verificación"""
        if not self.verification_state:
            if len(self.cedula_field.value) < 1:
                self.status_message.value = "✅ Ingrese el N° de cédula del cliente"
            else:
                # Mostrar mensaje de carga
                self.show_loading()
                
                # Ejecutar la consulta (esto podría hacerse en un hilo separado)
                try:
                    datos_cliente = get_client_by_cedula(
                        self.sheets_service, 
                        self.SPREADSHEET_ID, 
                        self.SHEET_NAME, 
                        self.cedula_field.value
                    )
                    self.cliente.update(datos_cliente)
                    
                    if datos_cliente:
                        self.verification_state = True
                        self.status_message.value = f"✅ Cliente Encontrado: {datos_cliente['Nombres y Apellidos completos como esta en tu Cedula.'].upper()}"
                    else:
                        #self.verification_state = True
                        self.status_message.value = f"❌ No se encontró ningún cliente con cédula {self.cedula_field.value}. Puede [registrar un cliente aquí](https://docs.google.com/forms/d/e/1FAIpQLSeGV6wC7fOgS13HD6yCbeAnQYsUuJC6TgOZrRzoCfrGVnTOQQ/viewform?usp=dialog)"
                except Exception as e:
                        self.status_message.value = f"❌ No se encontró ningún cliente con cédula {self.cedula_field.value}. Puede [registrar un cliente aquí](https://docs.google.com/forms/d/e/1FAIpQLSeGV6wC7fOgS13HD6yCbeAnQYsUuJC6TgOZrRzoCfrGVnTOQQ/viewform?usp=dialog)"
                finally:
                    # Restaurar botones
                    self.verify_button.disabled = False
                    self.reset_button.disabled = False
                    self.generate_button.disabled = False
        else:
            self.verification_state = False
            self.status_message.value = ""
            self.cedula_field.value = ""
        
        # Actualizar la interfaz
        self.verify_button.visible = not self.verification_state
        self.reset_button.visible = self.verification_state
        self.generate_button.visible = self.verification_state
        self.page.update()

    def generate_documents(self, e):
        try:
            limpiar_carpeta('Generado')
            self.show_loading("Creando carpeta personal...")
            Carpeta_Personal = process_client_data(self.drive_service, self.PARENT_FOLDER_ID, self.cliente)

            documentos = [
                ("Generando Formulario...", FORM_DATOS_NUEVOS_PARA_TRABAJADOR),
                ("Generando Carta de Poder...", Carta_Poder),
                ("Generando Carta de Compromiso...", Carta_Compromiso),
                ("Generando Desistimiento de renuncia...", Desistimiento_de_renuncia),
                ("Generando nota de renuncia...", Nota_de_Renuncia),
                ("Generando Documento de demanda...", documento_demanda)
            ]

            for mensaje, funcion in documentos:
                self.show_loading(mensaje)
                funcion(self.cliente)
                time.sleep(0.1)  # Usar await con asyncio.sleep

            self.show_loading("Subiendo archivos a Drive...")
            subir_archivos_a_drive(self.drive_service, 'Generado', Carpeta_Personal)

            # Mensaje de éxito y resetear estado
            self.status_message.value = f"✅ Documentos generados y subidos exitosamente! [Carpeta Generada](https://drive.google.com/drive/folders/{Carpeta_Personal})"

            self.verification_state = False  # Volver al estado inicial
            self.cedula_field.value = ""  # Limpiar campo de cédula

        except Exception as ex:
            self.status_message.value = f"❌ Error al generar documentos: {str(ex)}"
            print(f"Error completo: {traceback.format_exc()}")
        finally:
            # Restaurar estado de los botones
            self.verify_button.disabled = False
            self.reset_button.disabled = False
            self.generate_button.disabled = False

            # Actualizar visibilidad de botones
            self.verify_button.visible =  self.verification_state
            self.reset_button.visible = not self.verification_state
            self.generate_button.visible = self.verification_state

            self.page.update()


        
def main(page: ft.Page):

    app = DemandaLaboralApp(page)

# Ejecutar la aplicación
ft.app(target=main)
#FIN