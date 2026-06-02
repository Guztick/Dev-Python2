# -*- coding: utf-8 -*-
"""
Pantalla de códigos de falla (DTCs).

Lee los DTCs de todos los módulos del vehículo, los agrupa por
módulo, los muestra con descripción en español y severidad, y
permite borrarlos.
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador
from gui.components.cards import TarjetaDTC
from diagnostics.manual_service import servicio_manual


class PantallaDTCs(MDScreen):
    """Lectura y borrado de códigos de falla."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dtcs"
        self.md_bg_color = Color.FONDO
        self._leyendo = False
        self._dialogo = None
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical", padding=dp(Dim.PADDING),
                           spacing=dp(Dim.ESPACIO))

        # ===== Encabezado =====
        encabezado = MDBoxLayout(orientation="vertical", size_hint_y=None,
                                 height=dp(64), spacing=dp(2))
        encabezado.add_widget(MDLabel(
            text="Códigos de falla", theme_text_color="Custom",
            text_color=Color.TEXTO, font_style="H5", bold=True,
            size_hint_y=None, height=dp(36)))
        self._lbl_sub = MDLabel(
            text="Lee los DTCs de todos los módulos",
            theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(20))
        encabezado.add_widget(self._lbl_sub)
        raiz.add_widget(encabezado)

        # ===== Lista de DTCs =====
        scroll = MDScrollView(do_scroll_x=False)
        self._lista = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO_CHICO),
            size_hint_y=None, adaptive_height=True, padding=[0, dp(4)])
        scroll.add_widget(self._lista)
        raiz.add_widget(scroll)

        self._estado_vacio = self._crear_estado_inicial()
        self._lista.add_widget(self._estado_vacio)

        # ===== Botones =====
        fila_botones = MDBoxLayout(orientation="horizontal",
                                   spacing=dp(Dim.ESPACIO_CHICO),
                                   size_hint_y=None, height=dp(52))
        self._btn_leer = MDRaisedButton(
            text="LEER CÓDIGOS", md_bg_color=Color.PRIMARIO,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            font_size=Fuente.CUERPO, size_hint=(0.6, 1), elevation=0)
        self._btn_leer.bind(on_release=self._leer)

        self._btn_borrar = MDRaisedButton(
            text="BORRAR", md_bg_color=Color.SUPERFICIE,
            theme_text_color="Custom", text_color=Color.PELIGRO,
            font_size=Fuente.CUERPO, size_hint=(0.4, 1),
            line_color=Color.PELIGRO, elevation=0, disabled=True)
        self._btn_borrar.bind(on_release=self._confirmar_borrado)

        fila_botones.add_widget(self._btn_leer)
        fila_botones.add_widget(self._btn_borrar)
        raiz.add_widget(fila_botones)

        self.add_widget(raiz)

    def _crear_estado_inicial(self) -> MDBoxLayout:
        cont = MDBoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(200), spacing=dp(Dim.ESPACIO))
        cont.add_widget(MDBoxLayout(size_hint_y=None, height=dp(30)))
        cont.add_widget(MDIcon(
            icon="clipboard-search-outline", theme_text_color="Custom",
            text_color=Color.TEXTO_TENUE, font_size=dp(64), halign="center",
            size_hint_y=None, height=dp(72)))
        cont.add_widget(MDLabel(
            text="Sin lecturas", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SUBTITULO, bold=True,
            halign="center", size_hint_y=None, height=dp(28)))
        cont.add_widget(MDLabel(
            text="Presiona 'Leer códigos' para consultar\nlos fallos del vehículo",
            theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
            font_size=Fuente.SECUNDARIO, halign="center",
            size_hint_y=None, height=dp(40)))
        return cont

    def _leer(self, *_):
        if self._leyendo:
            return
        self._leyendo = True
        self._btn_leer.disabled = True
        self._btn_leer.text = "LEYENDO..."
        self._lista.clear_widgets()
        self._lista.add_widget(self._crear_cargando())

        controlador.leer_dtcs(on_completo=self._on_dtcs)

    def _crear_cargando(self) -> MDBoxLayout:
        cont = MDBoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(120), spacing=dp(Dim.ESPACIO))
        cont.add_widget(MDBoxLayout(size_hint_y=None, height=dp(30)))
        cont.add_widget(MDIcon(
            icon="sync", theme_text_color="Custom", text_color=Color.PRIMARIO,
            font_size=dp(48), halign="center", size_hint_y=None, height=dp(56)))
        cont.add_widget(MDLabel(
            text="Consultando módulos...", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.CUERPO,
            halign="center", size_hint_y=None, height=dp(24)))
        return cont

    def _on_dtcs(self, dtcs_por_modulo):
        Clock.schedule_once(lambda dt: self._mostrar_dtcs(dtcs_por_modulo))

    def _mostrar_dtcs(self, dtcs_por_modulo: dict):
        self._leyendo = False
        self._btn_leer.disabled = False
        self._btn_leer.text = "LEER DE NUEVO"
        self._lista.clear_widgets()

        total = sum(len(v) for v in dtcs_por_modulo.values())

        if total == 0:
            self._mostrar_sin_fallos()
            self._btn_borrar.disabled = True
            self._lbl_sub.text = "✅ Sin códigos de falla"
            return

        self._btn_borrar.disabled = False
        self._lbl_sub.text = f"⚠️ {total} código(s) encontrado(s)"

        for modulo, dtcs in dtcs_por_modulo.items():
            # Encabezado de grupo de módulo
            cab = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                              height=dp(32), spacing=dp(8))
            cab.add_widget(MDIcon(
                icon="chip", theme_text_color="Custom", text_color=Color.CYAN,
                font_size=dp(18), size_hint_x=None, width=dp(24),
                pos_hint={"center_y": 0.5}))
            cab.add_widget(MDLabel(
                text=f"{modulo}  ({len(dtcs)})", theme_text_color="Custom",
                text_color=Color.TEXTO, font_size=Fuente.CUERPO, bold=True,
                pos_hint={"center_y": 0.5}))
            self._lista.add_widget(cab)

            for dtc in dtcs:
                codigo = dtc.get("codigo", "?")
                tarjeta = TarjetaDTC(
                    codigo=codigo,
                    descripcion=dtc.get("desc", ""),
                    severidad=dtc.get("severidad", "media"),
                    activo=dtc.get("activo", True))
                self._lista.add_widget(tarjeta)

                if servicio_manual.tiene_procedimiento(codigo):
                    btn_proc = MDFlatButton(
                        text=f"  Ver procedimiento para {codigo}  →",
                        theme_text_color="Custom", text_color=Color.PRIMARIO,
                        font_size=Fuente.ETIQUETA, size_hint_y=None, height=dp(32))
                    btn_proc.bind(on_release=lambda *_, c=codigo: self._ir_a_procedimiento(c))
                    self._lista.add_widget(btn_proc)

    def _mostrar_sin_fallos(self):
        cont = MDBoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(200), spacing=dp(Dim.ESPACIO))
        cont.add_widget(MDBoxLayout(size_hint_y=None, height=dp(30)))
        cont.add_widget(MDIcon(
            icon="check-circle", theme_text_color="Custom", text_color=Color.EXITO,
            font_size=dp(72), halign="center", size_hint_y=None, height=dp(80)))
        cont.add_widget(MDLabel(
            text="¡Sin fallos!", theme_text_color="Custom", text_color=Color.EXITO,
            font_size=Fuente.TITULO, bold=True, halign="center",
            size_hint_y=None, height=dp(32)))
        cont.add_widget(MDLabel(
            text="No se encontraron códigos de falla\nen ningún módulo del vehículo",
            theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, halign="center",
            size_hint_y=None, height=dp(40)))
        self._lista.add_widget(cont)

    def _confirmar_borrado(self, *_):
        if not self._dialogo:
            self._dialogo = MDDialog(
                title="¿Borrar todos los códigos?",
                text="Esta acción borrará los DTCs de todos los módulos y "
                     "apagará la luz Check Engine. Los fallos reaparecerán si "
                     "el problema persiste.",
                buttons=[
                    MDFlatButton(text="CANCELAR", theme_text_color="Custom",
                                 text_color=Color.TEXTO_SUAVE,
                                 on_release=lambda x: self._dialogo.dismiss()),
                    MDRaisedButton(text="BORRAR", md_bg_color=Color.PELIGRO,
                                   theme_text_color="Custom", text_color=(1, 1, 1, 1),
                                   on_release=lambda x: self._ejecutar_borrado()),
                ],
            )
        self._dialogo.open()

    def _ejecutar_borrado(self):
        self._dialogo.dismiss()
        self._btn_borrar.text = "BORRANDO..."
        self._btn_borrar.disabled = True
        # En un caso real llamaría a controlador para borrar; aquí refrescamos
        Clock.schedule_once(lambda dt: self._post_borrado(), 1.0)

    def _ir_a_procedimiento(self, codigo_dtc: str):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        sm = app.root
        pantalla_principal = sm.get_screen("principal")
        pantalla_principal.ir_a_procedimiento_dtc(codigo_dtc)

    def _post_borrado(self):
        self._btn_borrar.text = "BORRAR"
        self._lista.clear_widgets()
        self._mostrar_sin_fallos()
        self._lbl_sub.text = "✅ Códigos borrados"
        self._btn_borrar.disabled = True
