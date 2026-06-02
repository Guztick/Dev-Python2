# -*- coding: utf-8 -*-
"""
Pantalla de información del adaptador (escáner).

Muestra los detalles técnicos del adaptador OBD-II conectado:
versión, chip, autenticidad, voltaje y los protocolos que soporta.
Permite al usuario conocer el alcance real de su escáner.
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador


class FilaDato(MDBoxLayout):
    """Fila de un dato técnico: etiqueta a la izquierda, valor a la derecha."""

    def __init__(self, etiqueta, valor, color_valor=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.add_widget(MDLabel(
            text=etiqueta, theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_x=0.42))
        self.add_widget(MDLabel(
            text=str(valor), theme_text_color="Custom",
            text_color=color_valor or Color.TEXTO, font_size=Fuente.CUERPO,
            bold=True, halign="right"))


class PantallaAdaptador(MDScreen):
    """Detalles técnicos del adaptador conectado."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "adaptador"
        self.md_bg_color = Color.FONDO
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical", padding=dp(Dim.PADDING),
                           spacing=dp(Dim.ESPACIO))

        # Encabezado
        encabezado = MDBoxLayout(orientation="vertical", size_hint_y=None,
                                 height=dp(64), spacing=dp(2))
        encabezado.add_widget(MDLabel(
            text="Información del escáner", theme_text_color="Custom",
            text_color=Color.TEXTO, font_style="H5", bold=True,
            size_hint_y=None, height=dp(36)))
        encabezado.add_widget(MDLabel(
            text="Detalles técnicos y alcance del adaptador",
            theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(20)))
        raiz.add_widget(encabezado)

        scroll = MDScrollView(do_scroll_x=False)
        self._contenido = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO),
            size_hint_y=None, adaptive_height=True, padding=[0, dp(4)])
        scroll.add_widget(self._contenido)
        raiz.add_widget(scroll)

        # Botón de detectar
        self._btn = MDRaisedButton(
            text="DETECTAR ADAPTADOR", md_bg_color=Color.PRIMARIO,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            font_size=Fuente.CUERPO, size_hint=(1, None), height=dp(52),
            elevation=0)
        self._btn.bind(on_release=self._detectar)
        raiz.add_widget(self._btn)

        self.add_widget(raiz)
        self._mostrar_estado_inicial()

    def _mostrar_estado_inicial(self):
        self._contenido.clear_widgets()
        cont = MDBoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(180), spacing=dp(Dim.ESPACIO))
        cont.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))
        cont.add_widget(MDIcon(
            icon="card-search-outline", theme_text_color="Custom",
            text_color=Color.TEXTO_TENUE, font_size=dp(64), halign="center",
            size_hint_y=None, height=dp(72)))
        cont.add_widget(MDLabel(
            text="Adaptador sin analizar", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SUBTITULO, bold=True,
            halign="center", size_hint_y=None, height=dp(28)))
        cont.add_widget(MDLabel(
            text="Presiona 'Detectar adaptador' para ver\nlos detalles de tu escáner",
            theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
            font_size=Fuente.SECUNDARIO, halign="center",
            size_hint_y=None, height=dp(40)))
        self._contenido.add_widget(cont)

    def _detectar(self, *_):
        self._btn.disabled = True
        self._btn.text = "DETECTANDO..."
        self._contenido.clear_widgets()
        cargando = MDBoxLayout(orientation="vertical", size_hint_y=None,
                               height=dp(120))
        cargando.add_widget(MDIcon(
            icon="sync", theme_text_color="Custom", text_color=Color.PRIMARIO,
            font_size=dp(48), halign="center", size_hint_y=None, height=dp(60)))
        cargando.add_widget(MDLabel(
            text="Interrogando al adaptador...", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.CUERPO,
            halign="center"))
        self._contenido.add_widget(cargando)

        controlador.detectar_adaptador(
            on_completo=lambda info: Clock.schedule_once(
                lambda dt: self._mostrar_info(info)))

    def _mostrar_info(self, info):
        self._btn.disabled = False
        self._btn.text = "DETECTAR DE NUEVO"
        self._contenido.clear_widgets()

        if info is None:
            self._mostrar_estado_inicial()
            return

        # ===== Tarjeta de resumen con badge de autenticidad =====
        color_auth = Color.EXITO if info.es_genuino else (
            Color.ADVERTENCIA if info.es_genuino is False else Color.TEXTO_SUAVE)
        texto_auth = ("GENUINO" if info.es_genuino else
                      "CLON" if info.es_genuino is False else "INDETERMINADO")

        tarjeta_res = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)], size_hint_y=None, height=dp(120),
            padding=dp(Dim.PADDING), spacing=dp(Dim.ESPACIO_CHICO),
            elevation=0, line_color=Color.BORDE, line_width=1)

        fila_top = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(48), spacing=dp(Dim.ESPACIO))
        cont_ic = MDCard(
            md_bg_color=(Color.PRIMARIO[0], Color.PRIMARIO[1], Color.PRIMARIO[2], 0.15),
            radius=[dp(Dim.RADIO_CHICO)], size_hint=(None, None),
            size=(dp(48), dp(48)), elevation=0)
        cont_ic.add_widget(MDIcon(
            icon="usb-flash-drive", theme_text_color="Custom",
            text_color=Color.PRIMARIO, font_size=dp(26),
            pos_hint={"center_x": 0.5, "center_y": 0.5}))
        col = MDBoxLayout(orientation="vertical", pos_hint={"center_y": 0.5})
        col.add_widget(MDLabel(
            text=info.identidad or "Adaptador OBD-II", theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
            size_hint_y=None, height=dp(26)))
        col.add_widget(MDLabel(
            text=info.fabricante_chip, theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SECUNDARIO,
            size_hint_y=None, height=dp(20)))
        # Badge
        badge = MDCard(
            md_bg_color=(color_auth[0], color_auth[1], color_auth[2], 0.18),
            radius=[dp(12)], size_hint=(None, None), size=(dp(96), dp(28)),
            pos_hint={"center_y": 0.5}, elevation=0, padding=[dp(8), 0])
        badge.add_widget(MDLabel(
            text=texto_auth, theme_text_color="Custom", text_color=color_auth,
            font_size=Fuente.ETIQUETA, bold=True, halign="center"))
        fila_top.add_widget(cont_ic)
        fila_top.add_widget(col)
        fila_top.add_widget(badge)

        tarjeta_res.add_widget(fila_top)
        tarjeta_res.add_widget(MDLabel(
            text=info.nivel_calidad(), theme_text_color="Custom",
            text_color=color_auth, font_size=Fuente.SECUNDARIO,
            size_hint_y=None, height=dp(36)))
        self._contenido.add_widget(tarjeta_res)

        # ===== Tarjeta de datos técnicos =====
        tarjeta_datos = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
            padding=dp(Dim.PADDING), elevation=0,
            line_color=Color.BORDE, line_width=1)
        tarjeta_datos.add_widget(MDLabel(
            text="Datos técnicos", theme_text_color="Custom", text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO, bold=True, size_hint_y=None, height=dp(32)))

        datos = [
            ("Versión ELM", info.version_elm or "N/D", None),
            ("Conexión", info.tipo_conexion or "N/D", None),
            ("Voltaje leído", f"{info.voltaje:.1f} V" if info.voltaje else "N/D",
             Color.EXITO if info.voltaje and info.voltaje >= 12.4 else None),
            ("Protocolo actual", (info.protocolo_actual or "N/D").replace(
                "ISO 15765-4 ", "")[:28], Color.CYAN),
            ("Protocolos soportados", f"{len(info.protocolos_soportados)}", None),
        ]
        for etiqueta, valor, color in datos:
            tarjeta_datos.add_widget(FilaDato(etiqueta, valor, color))
        self._contenido.add_widget(tarjeta_datos)

        # ===== Lista de protocolos soportados =====
        tarjeta_proto = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
            padding=dp(Dim.PADDING), spacing=dp(4), elevation=0,
            line_color=Color.BORDE, line_width=1)
        tarjeta_proto.add_widget(MDLabel(
            text="Protocolos compatibles", theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
            size_hint_y=None, height=dp(32)))
        for proto in info.protocolos_soportados:
            fila = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(28), spacing=dp(8))
            fila.add_widget(MDIcon(
                icon="check", theme_text_color="Custom", text_color=Color.EXITO,
                font_size=dp(16), size_hint_x=None, width=dp(22),
                pos_hint={"center_y": 0.5}))
            fila.add_widget(MDLabel(
                text=proto, theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
                font_size=Fuente.SECUNDARIO, pos_hint={"center_y": 0.5}))
            tarjeta_proto.add_widget(fila)
        self._contenido.add_widget(tarjeta_proto)
