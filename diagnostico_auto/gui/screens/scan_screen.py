# -*- coding: utf-8 -*-
"""
Pantalla de escaneo de capacidades.

Ejecuta el escaneo del vehículo módulo por módulo y muestra el
resultado: qué ECUs están presentes y qué nivel de acceso tiene
cada uno. Es la función estrella de la herramienta.
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador
from gui.components.cards import TarjetaModulo


class PantallaEscaneo(MDScreen):
    """Escaneo de capacidades del vehículo."""

    def __init__(self, on_resultado=None, **kwargs):
        super().__init__(**kwargs)
        self.name = "escaneo"
        self.md_bg_color = Color.FONDO
        self._on_resultado = on_resultado or (lambda d, m: None)
        self._escaneando = False
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(
            orientation="vertical",
            padding=dp(Dim.PADDING),
            spacing=dp(Dim.ESPACIO),
        )

        # ===== Encabezado =====
        encabezado = MDBoxLayout(orientation="vertical", size_hint_y=None,
                                 height=dp(64), spacing=dp(2))
        encabezado.add_widget(MDLabel(
            text="Escaneo de capacidades", theme_text_color="Custom",
            text_color=Color.TEXTO, font_style="H5", bold=True,
            size_hint_y=None, height=dp(36)))
        encabezado.add_widget(MDLabel(
            text="Detecta los módulos ECU y su nivel de acceso",
            theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(20)))
        raiz.add_widget(encabezado)

        # ===== Barra de progreso =====
        self._cont_progreso = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None, height=dp(72),
            padding=dp(Dim.PADDING), spacing=dp(Dim.ESPACIO_CHICO),
            elevation=0, line_color=Color.BORDE, line_width=1, opacity=0)
        self._lbl_progreso = MDLabel(
            text="Preparando...", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SECUNDARIO,
            size_hint_y=None, height=dp(20))
        self._barra = MDProgressBar(
            value=0, color=Color.PRIMARIO, size_hint_y=None, height=dp(6))
        self._cont_progreso.add_widget(self._lbl_progreso)
        self._cont_progreso.add_widget(self._barra)
        raiz.add_widget(self._cont_progreso)

        # ===== Lista de resultados =====
        scroll = MDScrollView(do_scroll_x=False)
        self._lista = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO_CHICO),
            size_hint_y=None, adaptive_height=True, padding=[0, dp(4)])
        scroll.add_widget(self._lista)
        raiz.add_widget(scroll)

        # Estado vacío inicial
        self._estado_vacio = self._crear_estado_vacio()
        self._lista.add_widget(self._estado_vacio)

        # ===== Botón de escanear =====
        self._btn = MDRaisedButton(
            text="INICIAR ESCANEO", md_bg_color=Color.PRIMARIO,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            font_size=Fuente.CUERPO, size_hint=(1, None), height=dp(52),
            elevation=0)
        self._btn.bind(on_release=self._iniciar_escaneo)
        raiz.add_widget(self._btn)

        self.add_widget(raiz)

    def _crear_estado_vacio(self) -> MDBoxLayout:
        cont = MDBoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(180), spacing=dp(Dim.ESPACIO))
        cont.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))
        cont.add_widget(MDIcon(
            icon="radar", theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
            font_size=dp(64), halign="center", size_hint_y=None, height=dp(72)))
        cont.add_widget(MDLabel(
            text="Sin escanear", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SUBTITULO,
            bold=True, halign="center", size_hint_y=None, height=dp(28)))
        cont.add_widget(MDLabel(
            text="Presiona 'Iniciar escaneo' para detectar\nlos módulos del vehículo",
            theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
            font_size=Fuente.SECUNDARIO, halign="center",
            size_hint_y=None, height=dp(40)))
        return cont

    def _iniciar_escaneo(self, *_):
        if self._escaneando:
            return
        self._escaneando = True
        self._btn.disabled = True
        self._btn.text = "ESCANEANDO..."
        self._lista.clear_widgets()
        self._cont_progreso.opacity = 1
        self._barra.value = 0

        controlador.escanear_capacidades(
            on_progreso=self._on_progreso,
            on_completo=self._on_completo,
        )

    def _on_progreso(self, mensaje: str, porcentaje: float):
        Clock.schedule_once(lambda dt: self._actualizar_progreso(mensaje, porcentaje))

    def _actualizar_progreso(self, mensaje: str, porcentaje: float):
        self._lbl_progreso.text = mensaje
        self._barra.value = porcentaje

    def _on_completo(self, resultado):
        Clock.schedule_once(lambda dt: self._mostrar_resultado(resultado))

    def _mostrar_resultado(self, resultado):
        self._escaneando = False
        self._btn.disabled = False
        self._btn.text = "ESCANEAR DE NUEVO"
        self._cont_progreso.opacity = 0
        self._lista.clear_widgets()

        if not resultado:
            self._lista.add_widget(self._crear_estado_vacio())
            return

        # Normalizar resultado (puede venir como lista de dicts del demo
        # o como ReporteEscaneo del hardware real)
        modulos = self._normalizar(resultado)
        presentes = [m for m in modulos if m["presente"]]
        total_dtcs = sum(m["dtcs"] for m in presentes)

        # Resumen superior
        resumen = MDCard(
            orientation="horizontal", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None, height=dp(56),
            padding=dp(Dim.PADDING), elevation=0,
            line_color=Color.BORDE, line_width=1)
        resumen.add_widget(MDIcon(
            icon="check-decagram", theme_text_color="Custom", text_color=Color.EXITO,
            font_size=dp(24), size_hint_x=None, width=dp(32),
            pos_hint={"center_y": 0.5}))
        resumen.add_widget(MDLabel(
            text=f"{len(presentes)} módulos detectados · {total_dtcs} DTCs",
            theme_text_color="Custom", text_color=Color.TEXTO,
            font_size=Fuente.CUERPO, bold=True, pos_hint={"center_y": 0.5}))
        self._lista.add_widget(resumen)

        # Tarjetas de módulos
        for mod in modulos:
            tarjeta = TarjetaModulo(
                nombre=mod["nombre"], descripcion=mod["desc"],
                nivel=mod["nivel"], num_dtcs=mod["dtcs"], presente=mod["presente"])
            self._lista.add_widget(tarjeta)

        # Notificar al dashboard
        self._on_resultado(total_dtcs, len(presentes))

    def _normalizar(self, resultado) -> list:
        """Convierte cualquier formato de resultado a lista uniforme de dicts."""
        if isinstance(resultado, list):
            return [{"nombre": m.get("nombre", "?"), "desc": m.get("desc", ""),
                     "nivel": m.get("nivel", 0), "dtcs": m.get("dtcs", 0),
                     "presente": m.get("presente", False)} for m in resultado]
        # ReporteEscaneo del hardware real
        modulos = []
        for cap in getattr(resultado, "modulos", []):
            nivel = 0
            na = cap.nivel_acceso
            if na.uds_seguro: nivel = 4
            elif na.uds_extendido: nivel = 3
            elif na.uds_default: nivel = 2
            elif na.obd2_basico: nivel = 1
            modulos.append({
                "nombre": cap.nombre, "desc": cap.descripcion,
                "nivel": nivel, "dtcs": cap.num_dtcs, "presente": cap.presente})
        return modulos
