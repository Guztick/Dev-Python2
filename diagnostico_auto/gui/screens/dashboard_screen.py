# -*- coding: utf-8 -*-
"""
Pantalla principal (Dashboard).

Centro de control de la app: muestra la información del vehículo
conectado, métricas rápidas y accesos directos a las funciones
de diagnóstico.
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.card import MDCard

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador
from gui.components.cards import TarjetaStat, TarjetaAccion


class PantallaDashboard(MDScreen):
    """Dashboard principal con info del vehículo y accesos a funciones."""

    def __init__(self, ir_a_seccion=None, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self.md_bg_color = Color.FONDO
        self._ir_a_seccion = ir_a_seccion or (lambda s: None)
        self._construir()

    def on_pre_enter(self, *_):
        """Refrescar datos cada vez que se entra a la pantalla."""
        self._actualizar_info()

    def _construir(self):
        scroll = MDScrollView(do_scroll_x=False)
        raiz = MDBoxLayout(
            orientation="vertical",
            padding=dp(Dim.PADDING),
            spacing=dp(Dim.ESPACIO),
            size_hint_y=None,
            adaptive_height=True,
        )

        # ===== Tarjeta de cabecera del vehículo =====
        self._cabecera = self._crear_cabecera_vehiculo()
        raiz.add_widget(self._cabecera)

        # ===== Métricas rápidas (3 tarjetas) =====
        lbl_metricas = MDLabel(
            text="Estado general",
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO,
            bold=True,
            size_hint_y=None,
            height=dp(32),
        )
        raiz.add_widget(lbl_metricas)

        grid_stats = MDGridLayout(
            cols=3,
            spacing=dp(Dim.ESPACIO_CHICO),
            size_hint_y=None,
            height=dp(Dim.ALTURA_TARJETA + 28),
        )
        self._stat_voltaje = TarjetaStat(
            icono="car-battery", valor="--", etiqueta="Voltaje",
            color_acento=Color.EXITO)
        self._stat_dtcs = TarjetaStat(
            icono="alert-circle", valor="--", etiqueta="Códigos DTC",
            color_acento=Color.ADVERTENCIA)
        self._stat_modulos = TarjetaStat(
            icono="chip", valor="--", etiqueta="Módulos",
            color_acento=Color.CYAN)
        grid_stats.add_widget(self._stat_voltaje)
        grid_stats.add_widget(self._stat_dtcs)
        grid_stats.add_widget(self._stat_modulos)
        raiz.add_widget(grid_stats)

        # ===== Acciones de diagnóstico =====
        lbl_acciones = MDLabel(
            text="Diagnóstico",
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO,
            bold=True,
            size_hint_y=None,
            height=dp(32),
        )
        raiz.add_widget(lbl_acciones)

        grid_acciones = MDGridLayout(
            cols=2,
            spacing=dp(Dim.ESPACIO_CHICO),
            size_hint_y=None,
            height=dp(132 * 2 + Dim.ESPACIO_CHICO),
        )
        acciones = [
            ("magnify-scan", "Escanear", "Detectar módulos y capacidades",
             Color.PRIMARIO, "escaneo"),
            ("alert-circle-outline", "Códigos DTC", "Leer y borrar fallos",
             Color.PELIGRO, "dtcs"),
            ("gauge", "Datos en vivo", "Sensores en tiempo real",
             Color.CYAN, "datos"),
            ("cog-play", "Actuadores", "Pruebas de componentes",
             Color.ADVERTENCIA, "actuadores"),
        ]
        for icono, titulo, desc, color, seccion in acciones:
            tarjeta = TarjetaAccion(
                icono=icono, titulo=titulo, descripcion=desc, color_acento=color)
            tarjeta.bind(on_release=lambda w, s=seccion: self._ir_a_seccion(s))
            grid_acciones.add_widget(tarjeta)
        raiz.add_widget(grid_acciones)

        scroll.add_widget(raiz)
        self.add_widget(scroll)

    def _crear_cabecera_vehiculo(self) -> MDCard:
        """Tarjeta destacada con la info del vehículo conectado."""
        tarjeta = MDCard(
            orientation="vertical",
            md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)],
            size_hint_y=None,
            height=dp(150),
            padding=dp(Dim.PADDING),
            spacing=dp(Dim.ESPACIO_CHICO),
            elevation=0,
            line_color=Color.BORDE,
            line_width=1,
        )

        # Fila superior: ícono + marca/modelo + estado conexión
        fila_sup = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(56), spacing=dp(Dim.ESPACIO))

        cont_icono = MDCard(
            md_bg_color=(Color.PRIMARIO[0], Color.PRIMARIO[1], Color.PRIMARIO[2], 0.15),
            radius=[dp(Dim.RADIO_CHICO)],
            size_hint=(None, None), size=(dp(56), dp(56)), elevation=0,
        )
        cont_icono.add_widget(MDIcon(
            icon="car-side", theme_text_color="Custom", text_color=Color.PRIMARIO,
            font_size=dp(32), pos_hint={"center_x": 0.5, "center_y": 0.5}))

        col_nombre = MDBoxLayout(orientation="vertical", pos_hint={"center_y": 0.5})
        self._lbl_modelo = MDLabel(
            text="Renault Duster", theme_text_color="Custom", text_color=Color.TEXTO,
            font_size=Fuente.TITULO, bold=True, size_hint_y=None, height=dp(30))
        self._lbl_motor = MDLabel(
            text="--", theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(20))
        col_nombre.add_widget(self._lbl_modelo)
        col_nombre.add_widget(self._lbl_motor)

        chip_conexion = MDCard(
            md_bg_color=(Color.EXITO[0], Color.EXITO[1], Color.EXITO[2], 0.15),
            radius=[dp(12)], size_hint=(None, None), size=(dp(96), dp(28)),
            pos_hint={"center_y": 0.5}, elevation=0, padding=[dp(8), 0])
        fila_chip = MDBoxLayout(orientation="horizontal", spacing=dp(4))
        fila_chip.add_widget(MDIcon(
            icon="check-circle", theme_text_color="Custom", text_color=Color.EXITO,
            font_size=dp(14), size_hint_x=None, width=dp(16),
            pos_hint={"center_y": 0.5}))
        fila_chip.add_widget(MDLabel(
            text="En línea", theme_text_color="Custom", text_color=Color.EXITO,
            font_size=Fuente.ETIQUETA, bold=True, pos_hint={"center_y": 0.5}))
        chip_conexion.add_widget(fila_chip)

        fila_sup.add_widget(cont_icono)
        fila_sup.add_widget(col_nombre)
        fila_sup.add_widget(chip_conexion)

        # Divisor
        divisor = MDCard(md_bg_color=Color.BORDE, size_hint_y=None, height=dp(1),
                         radius=[0], elevation=0)

        # Fila inferior: VIN y protocolo
        fila_inf = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        col_vin = MDBoxLayout(orientation="vertical")
        col_vin.add_widget(MDLabel(
            text="VIN", theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
            font_size=Fuente.ETIQUETA, size_hint_y=None, height=dp(16)))
        self._lbl_vin = MDLabel(
            text="--", theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(20))
        col_vin.add_widget(self._lbl_vin)

        col_proto = MDBoxLayout(orientation="vertical")
        col_proto.add_widget(MDLabel(
            text="Protocolo", theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
            font_size=Fuente.ETIQUETA, size_hint_y=None, height=dp(16)))
        self._lbl_proto = MDLabel(
            text="--", theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.ETIQUETA, size_hint_y=None, height=dp(20))
        col_proto.add_widget(self._lbl_proto)

        fila_inf.add_widget(col_vin)
        fila_inf.add_widget(col_proto)

        tarjeta.add_widget(fila_sup)
        tarjeta.add_widget(divisor)
        tarjeta.add_widget(fila_inf)
        return tarjeta

    def _actualizar_info(self):
        info = controlador.info_vehiculo
        self._lbl_modelo.text = f"{info.marca} {info.modelo}"
        self._lbl_motor.text = info.motor or "Motor no identificado"
        self._lbl_vin.text = info.vin or "No disponible"
        self._lbl_proto.text = (info.protocolo or "--").replace("ISO 15765-4 ", "")

        if info.voltaje:
            self._stat_voltaje.valor = f"{info.voltaje:.1f}"
            color = Color.EXITO if info.voltaje >= 12.4 else Color.ADVERTENCIA
            self._stat_voltaje.color_acento = color
        else:
            self._stat_voltaje.valor = "--"

        # Estos valores se llenan tras un escaneo
        self._stat_dtcs.valor = "—"
        self._stat_modulos.valor = "—"

    def set_resumen(self, num_dtcs: int, num_modulos: int):
        """Actualiza las métricas tras un escaneo (llamado desde otras pantallas)."""
        self._stat_dtcs.valor = str(num_dtcs)
        self._stat_dtcs.color_acento = Color.PELIGRO if num_dtcs > 0 else Color.EXITO
        self._stat_modulos.valor = str(num_modulos)
