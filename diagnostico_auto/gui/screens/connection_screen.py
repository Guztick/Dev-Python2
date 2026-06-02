# -*- coding: utf-8 -*-
"""
Pantalla de conexión — punto de entrada de la app.

Permite seleccionar el tipo de adaptador (WiFi, Bluetooth, USB o Demo),
ingresar la dirección y conectar al vehículo. Muestra el estado de
conexión con retroalimentación visual clara.
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.relativelayout import MDRelativeLayout

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador, TipoAdaptador, EstadoConexion


class BotonAdaptador(MDCard):
    """Botón de selección de tipo de adaptador."""

    def __init__(self, icono, texto, tipo, on_select, **kwargs):
        super().__init__(**kwargs)
        self.tipo = tipo
        self._on_select = on_select
        self._seleccionado = False

        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(92)
        self.md_bg_color = Color.SUPERFICIE
        self.radius = [dp(Dim.RADIO_CHICO)]
        self.line_color = Color.BORDE
        self.line_width = 1
        self.elevation = 0
        self.padding = dp(Dim.PADDING_CHICO)
        self.spacing = dp(4)
        self.ripple_behavior = True

        self._icono = MDIcon(
            icon=icono,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=dp(32),
            halign="center",
            size_hint_y=None,
            height=dp(40),
        )
        self._texto = MDLabel(
            text=texto,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            bold=True,
            halign="center",
        )
        self.add_widget(self._icono)
        self.add_widget(self._texto)

    def on_release(self):
        self._on_select(self)

    def set_seleccionado(self, valor: bool):
        self._seleccionado = valor
        if valor:
            self.line_color = Color.PRIMARIO
            self.line_width = 2
            self.md_bg_color = (Color.PRIMARIO[0], Color.PRIMARIO[1],
                                Color.PRIMARIO[2], 0.12)
            self._icono.text_color = Color.PRIMARIO
            self._texto.text_color = Color.TEXTO
        else:
            self.line_color = Color.BORDE
            self.line_width = 1
            self.md_bg_color = Color.SUPERFICIE
            self._icono.text_color = Color.TEXTO_SUAVE
            self._texto.text_color = Color.TEXTO_SUAVE


class PantallaConexion(MDScreen):
    """Pantalla de selección de adaptador y conexión."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "conexion"
        self.md_bg_color = Color.FONDO
        self._tipo_seleccionado = TipoAdaptador.DEMO
        self._botones_adapt = []
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(
            orientation="vertical",
            padding=[dp(Dim.PADDING_GRANDE), dp(48),
                     dp(Dim.PADDING_GRANDE), dp(Dim.PADDING_GRANDE)],
            spacing=dp(Dim.ESPACIO),
        )

        # ===== Logo / encabezado =====
        cont_logo = MDBoxLayout(orientation="vertical", size_hint_y=None,
                                height=dp(140), spacing=dp(4))

        icono_app = MDIcon(
            icon="car-wrench",
            theme_text_color="Custom",
            text_color=Color.PRIMARIO,
            font_size=dp(64),
            halign="center",
            size_hint_y=None,
            height=dp(72),
        )
        titulo = MDLabel(
            text="DiagnósticoPro",
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_style="H4",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(40),
        )
        subtitulo = MDLabel(
            text="Herramienta de diagnóstico automotriz",
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            halign="center",
            size_hint_y=None,
            height=dp(20),
        )
        cont_logo.add_widget(icono_app)
        cont_logo.add_widget(titulo)
        cont_logo.add_widget(subtitulo)

        # ===== Selección de adaptador =====
        lbl_sel = MDLabel(
            text="Selecciona el tipo de adaptador",
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            size_hint_y=None,
            height=dp(24),
        )

        grid_adapt = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(Dim.ESPACIO_CHICO),
            size_hint_y=None,
            height=dp(92),
        )
        adaptadores = [
            ("wifi", "WiFi", TipoAdaptador.WIFI),
            ("bluetooth", "Bluetooth", TipoAdaptador.BLUETOOTH),
            ("usb", "USB", TipoAdaptador.USB),
            ("flask-outline", "Demo", TipoAdaptador.DEMO),
        ]
        for icono, texto, tipo in adaptadores:
            btn = BotonAdaptador(icono, texto, tipo, self._seleccionar_adaptador)
            self._botones_adapt.append(btn)
            grid_adapt.add_widget(btn)

        # ===== Campo de dirección =====
        self._campo_dir = MDTextField(
            hint_text="Dirección (IP / MAC / puerto)",
            helper_text="Modo demo no requiere dirección",
            helper_text_mode="on_focus",
            mode="rectangle",
            size_hint_y=None,
            height=dp(56),
            disabled=True,
        )

        # ===== Estado de conexión =====
        self._tarjeta_estado = MDCard(
            md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO_CHICO)],
            size_hint_y=None,
            height=dp(56),
            padding=dp(Dim.PADDING),
            elevation=0,
            line_color=Color.BORDE,
            line_width=1,
        )
        fila_estado = MDBoxLayout(orientation="horizontal", spacing=dp(Dim.ESPACIO))
        self._icono_estado = MDIcon(
            icon="circle-outline",
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=dp(20),
            size_hint_x=None,
            width=dp(28),
            pos_hint={"center_y": 0.5},
        )
        self._lbl_estado = MDLabel(
            text="Listo para conectar",
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.CUERPO,
            pos_hint={"center_y": 0.5},
        )
        fila_estado.add_widget(self._icono_estado)
        fila_estado.add_widget(self._lbl_estado)
        self._tarjeta_estado.add_widget(fila_estado)

        # ===== Botón de conectar =====
        self._btn_conectar = MDRaisedButton(
            text="CONECTAR",
            md_bg_color=Color.PRIMARIO,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_size=Fuente.CUERPO,
            size_hint=(1, None),
            height=dp(52),
            elevation=0,
        )
        self._btn_conectar.bind(on_release=self._conectar)

        # Espaciador flexible
        espaciador = MDBoxLayout()

        # Ensamblar
        raiz.add_widget(cont_logo)
        raiz.add_widget(MDBoxLayout(size_hint_y=None, height=dp(8)))
        raiz.add_widget(lbl_sel)
        raiz.add_widget(grid_adapt)
        raiz.add_widget(self._campo_dir)
        raiz.add_widget(espaciador)
        raiz.add_widget(self._tarjeta_estado)
        raiz.add_widget(self._btn_conectar)

        self.add_widget(raiz)

        # Seleccionar Demo por defecto
        self._botones_adapt[-1].set_seleccionado(True)

    def _seleccionar_adaptador(self, boton):
        for btn in self._botones_adapt:
            btn.set_seleccionado(btn is boton)
        self._tipo_seleccionado = boton.tipo

        # Habilitar campo de dirección salvo en modo demo
        es_demo = boton.tipo == TipoAdaptador.DEMO
        self._campo_dir.disabled = es_demo
        if boton.tipo == TipoAdaptador.WIFI:
            self._campo_dir.text = "192.168.0.10:35000"
            self._campo_dir.hint_text = "IP:Puerto del adaptador WiFi"
        elif boton.tipo == TipoAdaptador.BLUETOOTH:
            self._campo_dir.text = ""
            self._campo_dir.hint_text = "Dirección MAC (00:11:22:33:44:55)"
        elif boton.tipo == TipoAdaptador.USB:
            self._campo_dir.text = "/dev/ttyUSB0"
            self._campo_dir.hint_text = "Puerto serial"
        else:
            self._campo_dir.text = ""

    def _conectar(self, *_):
        self._btn_conectar.disabled = True
        self._btn_conectar.text = "CONECTANDO..."
        self._actualizar_estado(EstadoConexion.CONECTANDO, "Conectando al vehículo...")

        controlador.conectar(
            tipo=self._tipo_seleccionado,
            direccion=self._campo_dir.text.strip(),
            on_completo=self._on_conexion_completa,
        )

    def _on_conexion_completa(self, exito: bool, mensaje: str):
        # Volver al hilo principal de Kivy para tocar la UI
        Clock.schedule_once(lambda dt: self._procesar_resultado(exito, mensaje))

    def _procesar_resultado(self, exito: bool, mensaje: str):
        self._btn_conectar.disabled = False
        self._btn_conectar.text = "CONECTAR"
        if exito:
            self._actualizar_estado(EstadoConexion.CONECTADO, mensaje)
            Clock.schedule_once(lambda dt: self._ir_a_dashboard(), 0.6)
        else:
            self._actualizar_estado(EstadoConexion.ERROR, f"Error: {mensaje}")

    def _actualizar_estado(self, estado: EstadoConexion, mensaje: str):
        config = {
            EstadoConexion.DESCONECTADO: ("circle-outline", Color.TEXTO_SUAVE),
            EstadoConexion.CONECTANDO:   ("sync", Color.ADVERTENCIA),
            EstadoConexion.CONECTADO:    ("check-circle", Color.EXITO),
            EstadoConexion.ERROR:        ("alert-circle", Color.PELIGRO),
        }
        icono, color = config.get(estado, ("circle-outline", Color.TEXTO_SUAVE))
        self._icono_estado.icon = icono
        self._icono_estado.text_color = color
        self._lbl_estado.text = mensaje
        self._lbl_estado.text_color = color if estado == EstadoConexion.ERROR else Color.TEXTO
        self._tarjeta_estado.line_color = color if estado != EstadoConexion.DESCONECTADO else Color.BORDE

    def _ir_a_dashboard(self):
        self.manager.current = "principal"
