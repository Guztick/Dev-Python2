# -*- coding: utf-8 -*-
"""
Pantalla de manuales de taller — Renault Duster.

Tres secciones accesibles desde pestañas internas:
  1. Procedimientos — diagnóstico paso a paso ligado a DTCs
  2. Sistemas       — despiece por sistema con componentes y especificaciones
  3. Referencia     — valores normales de datos en vivo

Diseñada para usarse tanto desde el botón directo en la navbar como
desde PantallaDTCs al pulsar "Ver procedimiento" en un código.
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.screenmanager import NoTransition
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivy.uix.widget import Widget

from gui.theme import Color, Dim, Fuente
from diagnostics.manual_service import servicio_manual


# ──────────────────────────────────────────────────────────────────────────────
# Componentes auxiliares
# ──────────────────────────────────────────────────────────────────────────────

class ChipTab(MDCard):
    """Pestaña superior de navegación interna."""

    def __init__(self, texto, on_tap, activo=False, **kwargs):
        super().__init__(**kwargs)
        self._on_tap = on_tap
        self._texto = texto
        self.size_hint = (1, None)
        self.height = dp(40)
        self.elevation = 0
        self.radius = [dp(Dim.RADIO_CHICO)]
        self._set_activo(activo)
        lbl = MDLabel(
            text=texto, halign="center",
            theme_text_color="Custom",
            text_color=Color.TEXTO if activo else Color.TEXTO_SUAVE,
            font_size=Fuente.ETIQUETA, bold=activo)
        self._lbl = lbl
        self.add_widget(lbl)
        self.bind(on_release=self._pulsado)

    def _set_activo(self, activo: bool):
        self._activo = activo
        if activo:
            self.md_bg_color = (Color.PRIMARIO[0], Color.PRIMARIO[1],
                                Color.PRIMARIO[2], 0.20)
            self.line_color = Color.PRIMARIO
            self.line_width = 1.5
        else:
            self.md_bg_color = Color.SUPERFICIE
            self.line_color = Color.BORDE
            self.line_width = 1

    def activar(self, activo: bool):
        self._set_activo(activo)
        if hasattr(self, "_lbl"):
            self._lbl.text_color = Color.TEXTO if activo else Color.TEXTO_SUAVE
            self._lbl.bold = activo

    def _pulsado(self, *_):
        if self._on_tap:
            self._on_tap(self._texto)


class SeveridadBarra(Widget):
    """Barra de color de 4 dp a la izquierda según severidad."""

    _COLORES = {
        "critico": Color.PELIGRO,
        "peligro": Color.PELIGRO,
        "advertencia": Color.ADVERTENCIA,
        "info": Color.CYAN,
    }

    def __init__(self, severidad="advertencia", **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.width = dp(4)
        self._color = self._COLORES.get(severidad, Color.ADVERTENCIA)
        self.bind(pos=self._dibujar, size=self._dibujar)

    def _dibujar(self, *_):
        from kivy.graphics import Color as KColor, RoundedRectangle
        self.canvas.before.clear()
        with self.canvas.before:
            KColor(*self._color)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[dp(2)])


# ──────────────────────────────────────────────────────────────────────────────
# Sub-pantalla 1: Procedimientos
# ──────────────────────────────────────────────────────────────────────────────

class PasoProcCard(MDCard):
    """Tarjeta expandible de un paso de diagnóstico."""

    def __init__(self, paso, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.md_bg_color = Color.SUPERFICIE
        self.radius = [dp(Dim.RADIO_CHICO)]
        self.size_hint_y = None
        self.adaptive_height = True
        self.padding = dp(Dim.PADDING)
        self.spacing = dp(6)
        self.elevation = 0
        self.line_color = Color.BORDE
        self.line_width = 1

        # Cabecera del paso
        cab = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                          height=dp(32), spacing=dp(10))
        num_card = MDCard(
            md_bg_color=(Color.PRIMARIO[0], Color.PRIMARIO[1], Color.PRIMARIO[2], 0.18),
            radius=[dp(12)], size_hint=(None, None),
            size=(dp(26), dp(26)), elevation=0,
            pos_hint={"center_y": 0.5})
        num_card.add_widget(MDLabel(
            text=str(paso.num), halign="center",
            theme_text_color="Custom", text_color=Color.PRIMARIO,
            font_size=Fuente.ETIQUETA, bold=True))
        titulo_lbl = MDLabel(
            text=paso.titulo, theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.CUERPO, bold=True)
        cab.add_widget(num_card)
        cab.add_widget(titulo_lbl)
        self.add_widget(cab)

        # Detalle
        detalle = MDLabel(
            text=paso.detalle, theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SECUNDARIO,
            text_size=(None, None))
        detalle.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
        self.add_widget(detalle)

        # Herramienta
        if paso.herramienta:
            fila_h = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                 height=dp(22), spacing=dp(6))
            fila_h.add_widget(MDIcon(
                icon="toolbox-outline", theme_text_color="Custom",
                text_color=Color.CYAN, font_size=dp(14),
                size_hint_x=None, width=dp(18),
                pos_hint={"center_y": 0.5}))
            fila_h.add_widget(MDLabel(
                text=paso.herramienta, theme_text_color="Custom",
                text_color=Color.CYAN, font_size=Fuente.ETIQUETA,
                pos_hint={"center_y": 0.5}))
            self.add_widget(fila_h)

        # Imagen placeholder si está definida pero no existe
        if paso.imagen and not paso.ruta_imagen():
            ph = MDCard(
                md_bg_color=(0.15, 0.15, 0.2, 1),
                radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None,
                height=dp(56), elevation=0,
                line_color=Color.BORDE, line_width=1,
                padding=dp(8))
            ph_box = MDBoxLayout(orientation="horizontal", spacing=dp(8))
            ph_box.add_widget(MDIcon(
                icon="image-outline", theme_text_color="Custom",
                text_color=Color.TEXTO_TENUE, font_size=dp(20),
                size_hint_x=None, width=dp(24)))
            ph_box.add_widget(MDLabel(
                text=f"Imagen: {paso.imagen}\n(añade tu foto en database/manuales/images/)",
                theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
                font_size=Fuente.ETIQUETA))
            ph.add_widget(ph_box)
            self.add_widget(ph)


class PantallaProcedimientos(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "proc"
        self.md_bg_color = Color.FONDO
        self._proc_actual = None
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical",
                           padding=[dp(Dim.PADDING), dp(8), dp(Dim.PADDING), 0],
                           spacing=dp(Dim.ESPACIO))

        # Buscador
        self._campo_busqueda = MDTextField(
            hint_text="Buscar por código o sistema...",
            mode="rectangle",
            size_hint_y=None, height=dp(48),
            text_color_normal=Color.TEXTO,
            hint_text_color_normal=Color.TEXTO_TENUE,
            line_color_normal=Color.BORDE,
            fill_color_normal=Color.SUPERFICIE,
            fill_color_focus=Color.SUPERFICIE,
            font_size=Fuente.CUERPO)
        self._campo_busqueda.bind(text=self._on_busqueda)
        raiz.add_widget(self._campo_busqueda)

        # Lista de procedimientos
        self._scroll_lista = MDScrollView(do_scroll_x=False, size_hint=(1, 0.38))
        self._lista = MDBoxLayout(
            orientation="vertical", spacing=dp(6),
            size_hint_y=None, adaptive_height=True, padding=[0, dp(4)])
        self._scroll_lista.add_widget(self._lista)
        raiz.add_widget(self._scroll_lista)

        # Detalle del procedimiento seleccionado
        self._scroll_detalle = MDScrollView(do_scroll_x=False)
        self._detalle = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO),
            size_hint_y=None, adaptive_height=True, padding=[0, dp(4)])
        self._scroll_detalle.add_widget(self._detalle)
        raiz.add_widget(self._scroll_detalle)

        self.add_widget(raiz)
        self._poblar_lista(servicio_manual.todos_los_procedimientos())

    def _on_busqueda(self, instance, texto):
        if texto:
            procs = servicio_manual.buscar_procedimientos(texto)
        else:
            procs = servicio_manual.todos_los_procedimientos()
        self._poblar_lista(procs)

    def _poblar_lista(self, procedimientos):
        self._lista.clear_widgets()
        for proc in procedimientos:
            self._lista.add_widget(self._tarjeta_proc(proc))

    def _tarjeta_proc(self, proc):
        COLORES = {
            "critico": Color.PELIGRO,
            "peligro": Color.PELIGRO,
            "advertencia": Color.ADVERTENCIA,
            "info": Color.CYAN,
        }
        color_sev = COLORES.get(proc.color_severidad, Color.ADVERTENCIA)

        card = MDCard(
            orientation="horizontal", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None, height=dp(64),
            elevation=0, line_color=Color.BORDE, line_width=1)
        card.bind(on_release=lambda *_: self._mostrar_procedimiento(proc))

        barra = SeveridadBarra(proc.color_severidad)
        barra.size_hint_y = 1

        contenido = MDBoxLayout(
            orientation="vertical", padding=[dp(10), dp(6)],
            spacing=dp(2))
        fila_top = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(22), spacing=dp(8))
        codigo_chip = MDCard(
            md_bg_color=(color_sev[0], color_sev[1], color_sev[2], 0.18),
            radius=[dp(8)], size_hint=(None, None), size=(dp(58), dp(22)),
            elevation=0, padding=[dp(6), 0])
        codigo_chip.add_widget(MDLabel(
            text=proc.codigo_dtc, theme_text_color="Custom",
            text_color=color_sev, font_size=Fuente.ETIQUETA,
            bold=True, halign="center"))
        fila_top.add_widget(codigo_chip)
        fila_top.add_widget(MDLabel(
            text=proc.sistema, theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.ETIQUETA))
        contenido.add_widget(fila_top)
        contenido.add_widget(MDLabel(
            text=proc.titulo, theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.SECUNDARIO,
            bold=True))

        card.add_widget(barra)
        card.add_widget(contenido)
        return card

    def _mostrar_procedimiento(self, proc):
        self._proc_actual = proc
        self._detalle.clear_widgets()

        # Encabezado del procedimiento
        enc = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
            padding=dp(Dim.PADDING), spacing=dp(6),
            elevation=0, line_color=Color.BORDE, line_width=1)

        fila_tit = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(28), spacing=dp(10))
        fila_tit.add_widget(MDIcon(
            icon=proc.icono or "wrench", theme_text_color="Custom",
            text_color=Color.PRIMARIO, font_size=dp(22),
            size_hint_x=None, width=dp(26)))
        fila_tit.add_widget(MDLabel(
            text=proc.titulo, theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.CUERPO, bold=True))
        enc.add_widget(fila_tit)

        if proc.sintomas:
            enc.add_widget(MDLabel(
                text="Síntomas típicos:", theme_text_color="Custom",
                text_color=Color.TEXTO_SUAVE, font_size=Fuente.ETIQUETA,
                bold=True, size_hint_y=None, height=dp(18)))
            for sint in proc.sintomas:
                fila_s = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                     height=dp(18), spacing=dp(6))
                fila_s.add_widget(MDIcon(
                    icon="circle-small", theme_text_color="Custom",
                    text_color=Color.ADVERTENCIA, font_size=dp(14),
                    size_hint_x=None, width=dp(14)))
                fila_s.add_widget(MDLabel(
                    text=sint, theme_text_color="Custom",
                    text_color=Color.TEXTO_SUAVE, font_size=Fuente.ETIQUETA))
                enc.add_widget(fila_s)

        self._detalle.add_widget(enc)

        # Componentes involucrados
        if proc.componentes:
            comp_card = MDCard(
                orientation="vertical", md_bg_color=Color.SUPERFICIE,
                radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
                padding=dp(Dim.PADDING), spacing=dp(4),
                elevation=0, line_color=Color.BORDE, line_width=1)
            comp_card.add_widget(MDLabel(
                text="Componentes involucrados", theme_text_color="Custom",
                text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
                size_hint_y=None, height=dp(28)))
            for comp in proc.componentes:
                fila_c = MDBoxLayout(orientation="vertical", size_hint_y=None,
                                     height=dp(42))
                fila_c.add_widget(MDLabel(
                    text=comp.get("nombre", ""), theme_text_color="Custom",
                    text_color=Color.TEXTO, font_size=Fuente.SECUNDARIO, bold=True,
                    size_hint_y=None, height=dp(20)))
                fila_c.add_widget(MDLabel(
                    text=comp.get("ubicacion", ""), theme_text_color="Custom",
                    text_color=Color.TEXTO_SUAVE, font_size=Fuente.ETIQUETA,
                    size_hint_y=None, height=dp(18)))
                comp_card.add_widget(fila_c)
            self._detalle.add_widget(comp_card)

        # Pasos
        titulo_pasos = MDLabel(
            text=f"Procedimiento diagnóstico ({proc.num_pasos} pasos)",
            theme_text_color="Custom", text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO, bold=True,
            size_hint_y=None, height=dp(28))
        self._detalle.add_widget(titulo_pasos)

        for paso in proc.pasos:
            self._detalle.add_widget(PasoProcCard(paso))

    def mostrar_por_codigo(self, codigo_dtc: str):
        """Llamado externamente desde PantallaDTCs."""
        proc = servicio_manual.procedimiento(codigo_dtc)
        if proc:
            Clock.schedule_once(lambda dt: self._mostrar_procedimiento(proc))
        else:
            self._detalle.clear_widgets()
            self._detalle.add_widget(MDLabel(
                text=f"Sin procedimiento disponible para {codigo_dtc}",
                theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
                font_size=Fuente.CUERPO, halign="center"))


# ──────────────────────────────────────────────────────────────────────────────
# Sub-pantalla 2: Sistemas / Despiece
# ──────────────────────────────────────────────────────────────────────────────

class PantallaSistemas(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "sistemas"
        self.md_bg_color = Color.FONDO
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical",
                           padding=[dp(Dim.PADDING), dp(8), dp(Dim.PADDING), 0],
                           spacing=dp(Dim.ESPACIO))

        # Lista de sistemas
        scroll_sis = MDScrollView(do_scroll_x=False, size_hint=(1, 0.32))
        self._lista_sis = MDBoxLayout(
            orientation="vertical", spacing=dp(6),
            size_hint_y=None, adaptive_height=True)
        scroll_sis.add_widget(self._lista_sis)
        raiz.add_widget(scroll_sis)

        # Detalle del sistema
        scroll_det = MDScrollView(do_scroll_x=False)
        self._det = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO),
            size_hint_y=None, adaptive_height=True, padding=[0, dp(4)])
        scroll_det.add_widget(self._det)
        raiz.add_widget(scroll_det)

        self.add_widget(raiz)
        self._poblar_sistemas()

    def _poblar_sistemas(self):
        for sis in servicio_manual.todos_los_sistemas():
            card = MDCard(
                orientation="horizontal", md_bg_color=Color.SUPERFICIE,
                radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None, height=dp(60),
                elevation=0, line_color=Color.BORDE, line_width=1,
                padding=dp(10), spacing=dp(12))
            card.bind(on_release=lambda *_, s=sis: self._mostrar_sistema(s))

            ic_cont = MDCard(
                md_bg_color=(Color.PRIMARIO[0], Color.PRIMARIO[1], Color.PRIMARIO[2], 0.15),
                radius=[dp(Dim.RADIO_CHICO)], size_hint=(None, None),
                size=(dp(42), dp(42)), elevation=0,
                pos_hint={"center_y": 0.5})
            ic_cont.add_widget(MDIcon(
                icon=sis.icono, theme_text_color="Custom",
                text_color=Color.PRIMARIO, font_size=dp(22),
                pos_hint={"center_x": 0.5, "center_y": 0.5}))

            col = MDBoxLayout(orientation="vertical", spacing=dp(2))
            col.add_widget(MDLabel(
                text=sis.nombre, theme_text_color="Custom",
                text_color=Color.TEXTO, font_size=Fuente.SECUNDARIO, bold=True,
                size_hint_y=None, height=dp(22)))
            col.add_widget(MDLabel(
                text=f"{len(sis.componentes)} componentes",
                theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
                font_size=Fuente.ETIQUETA, size_hint_y=None, height=dp(16)))

            card.add_widget(ic_cont)
            card.add_widget(col)
            self._lista_sis.add_widget(card)

    def _mostrar_sistema(self, sis):
        self._det.clear_widgets()

        desc = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
            padding=dp(Dim.PADDING), spacing=dp(6),
            elevation=0, line_color=Color.BORDE, line_width=1)
        desc.add_widget(MDLabel(
            text=sis.nombre, theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
            size_hint_y=None, height=dp(28)))
        desc_lbl = MDLabel(
            text=sis.descripcion, theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SECUNDARIO)
        desc_lbl.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
        desc.add_widget(desc_lbl)
        self._det.add_widget(desc)

        # Componentes
        for comp in sis.componentes:
            ccard = MDCard(
                orientation="vertical", md_bg_color=Color.SUPERFICIE,
                radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None,
                adaptive_height=True, padding=dp(Dim.PADDING), spacing=dp(4),
                elevation=0, line_color=Color.BORDE, line_width=1)

            ccard.add_widget(MDLabel(
                text=comp.nombre, theme_text_color="Custom",
                text_color=Color.TEXTO, font_size=Fuente.CUERPO, bold=True,
                size_hint_y=None, height=dp(22)))

            loc_fila = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                   height=dp(18), spacing=dp(6))
            loc_fila.add_widget(MDIcon(
                icon="map-marker-outline", theme_text_color="Custom",
                text_color=Color.CYAN, font_size=dp(13),
                size_hint_x=None, width=dp(14)))
            loc_fila.add_widget(MDLabel(
                text=comp.ubicacion, theme_text_color="Custom",
                text_color=Color.CYAN, font_size=Fuente.ETIQUETA))
            ccard.add_widget(loc_fila)

            desc_comp = MDLabel(
                text=comp.descripcion, theme_text_color="Custom",
                text_color=Color.TEXTO_SUAVE, font_size=Fuente.ETIQUETA)
            desc_comp.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
            ccard.add_widget(desc_comp)

            if comp.par_apriete:
                fila_par = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                       height=dp(20), spacing=dp(6))
                fila_par.add_widget(MDIcon(
                    icon="wrench", theme_text_color="Custom",
                    text_color=Color.ADVERTENCIA, font_size=dp(13),
                    size_hint_x=None, width=dp(14)))
                fila_par.add_widget(MDLabel(
                    text=f"Par: {comp.par_apriete}",
                    theme_text_color="Custom", text_color=Color.ADVERTENCIA,
                    font_size=Fuente.ETIQUETA, bold=True))
                ccard.add_widget(fila_par)

            if comp.herramienta_especial:
                fila_he = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                      height=dp(20), spacing=dp(6))
                fila_he.add_widget(MDIcon(
                    icon="star-outline", theme_text_color="Custom",
                    text_color=Color.PRIMARIO, font_size=dp(13),
                    size_hint_x=None, width=dp(14)))
                fila_he.add_widget(MDLabel(
                    text=f"Herramienta especial: {comp.herramienta_especial}",
                    theme_text_color="Custom", text_color=Color.PRIMARIO,
                    font_size=Fuente.ETIQUETA))
                ccard.add_widget(fila_he)

            self._det.add_widget(ccard)

        # Especificaciones
        if sis.especificaciones:
            spec_card = MDCard(
                orientation="vertical", md_bg_color=Color.SUPERFICIE,
                radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
                padding=dp(Dim.PADDING), spacing=dp(4),
                elevation=0, line_color=Color.BORDE, line_width=1)
            spec_card.add_widget(MDLabel(
                text="Especificaciones técnicas", theme_text_color="Custom",
                text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
                size_hint_y=None, height=dp(28)))
            for clave, valor in sis.especificaciones.items():
                fila = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                   height=dp(24))
                fila.add_widget(MDLabel(
                    text=clave.replace("_", " ").capitalize(),
                    theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
                    font_size=Fuente.ETIQUETA, size_hint_x=0.45))
                fila.add_widget(MDLabel(
                    text=str(valor), theme_text_color="Custom",
                    text_color=Color.TEXTO, font_size=Fuente.ETIQUETA,
                    bold=True, halign="right"))
                spec_card.add_widget(fila)
            self._det.add_widget(spec_card)


# ──────────────────────────────────────────────────────────────────────────────
# Sub-pantalla 3: Valores de referencia
# ──────────────────────────────────────────────────────────────────────────────

class PantallaReferencia(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "referencia"
        self.md_bg_color = Color.FONDO
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical",
                           padding=[dp(Dim.PADDING), dp(8), dp(Dim.PADDING), 0],
                           spacing=dp(Dim.ESPACIO))

        scroll = MDScrollView(do_scroll_x=False)
        contenido = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO),
            size_hint_y=None, adaptive_height=True)
        scroll.add_widget(contenido)
        raiz.add_widget(scroll)
        self.add_widget(raiz)

        for grupo in servicio_manual.grupos_referencia():
            g_card = MDCard(
                orientation="vertical", md_bg_color=Color.SUPERFICIE,
                radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
                padding=dp(Dim.PADDING), spacing=dp(6),
                elevation=0, line_color=Color.BORDE, line_width=1)

            g_card.add_widget(MDLabel(
                text=grupo.nombre, theme_text_color="Custom",
                text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
                size_hint_y=None, height=dp(28)))

            for pid in grupo.pids:
                self._agregar_pid(g_card, pid)

            contenido.add_widget(g_card)

    def _agregar_pid(self, padre, pid: dict):
        fila_nom = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(22), spacing=dp(8))
        fila_nom.add_widget(MDIcon(
            icon="gauge", theme_text_color="Custom",
            text_color=Color.PRIMARIO, font_size=dp(14),
            size_hint_x=None, width=dp(16),
            pos_hint={"center_y": 0.5}))
        fila_nom.add_widget(MDLabel(
            text=pid.get("nombre", ""), theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.SECUNDARIO, bold=True,
            pos_hint={"center_y": 0.5}))
        padre.add_widget(fila_nom)

        ralenti = pid.get("ralenti", {})
        if ralenti and (ralenti.get("min") is not None):
            rango = f"{ralenti['min']} – {ralenti['max']} {pid.get('unidad', '')}"
            if ralenti.get("nota"):
                rango += f"  ({ralenti['nota']})"
            fila_v = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                 height=dp(18), spacing=dp(8), padding=[dp(22), 0, 0, 0])
            fila_v.add_widget(MDLabel(
                text="Ralentí:", theme_text_color="Custom",
                text_color=Color.TEXTO_SUAVE, font_size=Fuente.ETIQUETA,
                size_hint_x=None, width=dp(52)))
            fila_v.add_widget(MDLabel(
                text=rango, theme_text_color="Custom",
                text_color=Color.EXITO, font_size=Fuente.ETIQUETA, bold=True))
            padre.add_widget(fila_v)

        comentario = pid.get("comentario", "")
        if comentario:
            com_lbl = MDLabel(
                text=comentario, theme_text_color="Custom",
                text_color=Color.TEXTO_TENUE, font_size=Fuente.ETIQUETA,
                padding=[dp(22), 0, 0, 0])
            com_lbl.bind(width=lambda i, w: setattr(i, "text_size", (w - dp(22), None)))
            padre.add_widget(com_lbl)

        # Separador fino
        sep = Widget(size_hint_y=None, height=dp(1))
        from kivy.graphics import Color as KC, Rectangle
        with sep.canvas:
            KC(*Color.BORDE)
            Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda w, _: w.canvas.clear() or
                 w.canvas.__enter__() or KC(*Color.BORDE) or
                 Rectangle(pos=w.pos, size=w.size) or w.canvas.__exit__(None, None, None))
        padre.add_widget(sep)


# ──────────────────────────────────────────────────────────────────────────────
# Pantalla principal del manual
# ──────────────────────────────────────────────────────────────────────────────

class PantallaManual(MDScreen):
    """
    Pantalla raíz del manual de taller. Gestiona las tres sub-secciones
    con pestañas superiores.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "manual"
        self.md_bg_color = Color.FONDO
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical")

        # Encabezado
        enc = MDBoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(70),
            padding=[dp(Dim.PADDING), dp(10), dp(Dim.PADDING), 0], spacing=dp(2))
        stats = servicio_manual.estadisticas()
        enc.add_widget(MDLabel(
            text="Manual de taller", theme_text_color="Custom",
            text_color=Color.TEXTO, font_style="H5", bold=True,
            size_hint_y=None, height=dp(36)))
        enc.add_widget(MDLabel(
            text=(f"Renault Duster  ·  {stats['procedimientos']} procedimientos  "
                  f"·  {stats['sistemas']} sistemas"),
            theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(20)))
        raiz.add_widget(enc)

        # Pestañas
        TABS = [("Procedimientos", "proc"),
                ("Sistemas", "sistemas"),
                ("Referencia", "referencia")]
        self._tabs: dict[str, ChipTab] = {}
        fila_tabs = MDBoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(48),
            padding=[dp(Dim.PADDING), dp(4)], spacing=dp(6))
        for nombre, nombre_screen in TABS:
            chip = ChipTab(nombre, on_tap=self._cambiar_tab,
                           activo=(nombre == "Procedimientos"))
            self._tabs[nombre] = chip
            fila_tabs.add_widget(chip)
        raiz.add_widget(fila_tabs)

        # Gestor de sub-pantallas
        self._sm = MDScreenManager(transition=NoTransition())
        self._pantalla_proc = PantallaProcedimientos()
        self._pantalla_sis = PantallaSistemas()
        self._pantalla_ref = PantallaReferencia()
        for s in (self._pantalla_proc, self._pantalla_sis, self._pantalla_ref):
            self._sm.add_widget(s)
        self._sm.current = "proc"
        raiz.add_widget(self._sm)

        self.add_widget(raiz)

    def _cambiar_tab(self, nombre_tab: str):
        MAPA = {
            "Procedimientos": "proc",
            "Sistemas": "sistemas",
            "Referencia": "referencia",
        }
        for n, chip in self._tabs.items():
            chip.activar(n == nombre_tab)
        self._sm.current = MAPA.get(nombre_tab, "proc")

    def ir_a_procedimiento(self, codigo_dtc: str):
        """
        Navega directamente a la pestaña de procedimientos y muestra
        el procedimiento del DTC indicado. Llamado desde PantallaDTCs.
        """
        self._cambiar_tab("Procedimientos")
        self._pantalla_proc.mostrar_por_codigo(codigo_dtc)
