# -*- coding: utf-8 -*-
"""
Componentes de tarjeta reutilizables.

Tarjetas con estilo Material consistente para mostrar información
de forma profesional en toda la aplicación.
"""
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from gui.theme import Color, Dim, Fuente


class TarjetaBase(MDCard):
    """Tarjeta base con el estilo de la app (fondo, radio, borde sutil)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = Color.SUPERFICIE
        self.radius = [dp(Dim.RADIO)]
        self.elevation = 0
        self.line_color = Color.BORDE
        self.line_width = 1
        self.padding = dp(Dim.PADDING)
        self.ripple_behavior = False


class TarjetaPresionable(MDCard):
    """
    Tarjeta base presionable. MDCard ya incluye comportamiento de ripple,
    pero no de botón, así que registramos un evento 'on_release' propio y
    lo disparamos al soltar el toque dentro de los límites de la tarjeta.
    """

    __events__ = ("on_release",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = Color.SUPERFICIE
        self.radius = [dp(Dim.RADIO)]
        self.elevation = 0
        self.line_color = Color.BORDE
        self.line_width = 1
        self.padding = dp(Dim.PADDING)
        self._presionado = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._presionado = True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._presionado and self.collide_point(*touch.pos):
            self._presionado = False
            self.dispatch("on_release")
        self._presionado = False
        return super().on_touch_up(touch)

    def on_release(self):
        """Evento disparado al pulsar la tarjeta (se sobrescribe con bind)."""


class TarjetaStat(TarjetaBase):
    """
    Tarjeta de estadística: ícono + valor grande + etiqueta.
    Usada en el dashboard para métricas rápidas (voltaje, DTCs, etc.).
    """
    icono = StringProperty("information")
    valor = StringProperty("--")
    etiqueta = StringProperty("")
    color_acento = ListProperty(Color.PRIMARIO)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(Dim.ESPACIO_CHICO)
        self.size_hint_y = None
        self.height = dp(Dim.ALTURA_TARJETA + 28)
        self._construir()

    def _construir(self):
        from kivymd.uix.label import MDIcon

        self._icono_w = MDIcon(
            icon=self.icono,
            theme_text_color="Custom",
            text_color=self.color_acento,
            font_size=dp(26),
            size_hint_y=None,
            height=dp(30),
        )
        self._valor_w = MDLabel(
            text=self.valor,
            font_style="H4",
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            bold=True,
            size_hint_y=None,
            height=dp(40),
        )
        self._etiqueta_w = MDLabel(
            text=self.etiqueta,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            size_hint_y=None,
            height=dp(18),
        )
        self.add_widget(self._icono_w)
        self.add_widget(self._valor_w)
        self.add_widget(self._etiqueta_w)

    def on_valor(self, *_):
        if hasattr(self, "_valor_w"):
            self._valor_w.text = self.valor

    def on_etiqueta(self, *_):
        if hasattr(self, "_etiqueta_w"):
            self._etiqueta_w.text = self.etiqueta

    def on_color_acento(self, *_):
        if hasattr(self, "_icono_w"):
            self._icono_w.text_color = self.color_acento


class TarjetaAccion(TarjetaPresionable):
    """
    Tarjeta de acción presionable: ícono grande + título + descripción.
    Usada en el dashboard como botones de función principales.
    """
    icono = StringProperty("car")
    titulo = StringProperty("Acción")
    descripcion = StringProperty("")
    color_acento = ListProperty(Color.PRIMARIO)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(Dim.ESPACIO_CHICO)
        self.size_hint_y = None
        self.height = dp(132)
        self.ripple_behavior = True
        self._construir()

    def _construir(self):
        from kivymd.uix.label import MDIcon
        from kivymd.uix.relativelayout import MDRelativeLayout

        # Contenedor del ícono con fondo de color tenue
        cont_icono = MDCard(
            md_bg_color=(self.color_acento[0], self.color_acento[1],
                         self.color_acento[2], 0.15),
            radius=[dp(Dim.RADIO_CHICO)],
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            elevation=0,
        )
        self._icono_w = MDIcon(
            icon=self.icono,
            theme_text_color="Custom",
            text_color=self.color_acento,
            font_size=dp(26),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        cont_icono.add_widget(self._icono_w)

        self._titulo_w = MDLabel(
            text=self.titulo,
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO,
            bold=True,
            size_hint_y=None,
            height=dp(24),
        )
        self._desc_w = MDLabel(
            text=self.descripcion,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            size_hint_y=None,
            height=dp(20),
        )

        self.add_widget(cont_icono)
        self.add_widget(self._titulo_w)
        self.add_widget(self._desc_w)


class TarjetaDTC(TarjetaBase):
    """
    Tarjeta para mostrar un código de falla (DTC).
    Indicador de severidad por color + código + descripción + estado.
    """
    codigo = StringProperty("P0000")
    descripcion = StringProperty("")
    severidad = StringProperty("media")   # baja / media / alta
    activo = BooleanProperty(True)

    COLORES_SEVERIDAD = {
        "baja":  Color.INFO,
        "media": Color.ADVERTENCIA,
        "alta":  Color.PELIGRO,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(Dim.ESPACIO)
        self.size_hint_y = None
        self.height = dp(84)
        self.padding = [dp(Dim.PADDING), dp(Dim.PADDING_CHICO)]
        self._construir()

    def _construir(self):
        color_sev = self.COLORES_SEVERIDAD.get(self.severidad, Color.ADVERTENCIA)

        # Barra de severidad lateral
        barra = MDCard(
            md_bg_color=color_sev,
            radius=[dp(3)],
            size_hint=(None, 1),
            width=dp(5),
            elevation=0,
        )

        # Columna de texto
        columna = MDBoxLayout(orientation="vertical", spacing=dp(2))

        fila_sup = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        cod_label = MDLabel(
            text=self.codigo,
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO,
            bold=True,
            size_hint_x=None,
            width=dp(80),
        )
        estado_chip = MDLabel(
            text="● ACTIVO" if self.activo else "○ HISTORIAL",
            theme_text_color="Custom",
            text_color=color_sev if self.activo else Color.TEXTO_SUAVE,
            font_size=Fuente.ETIQUETA,
            bold=True,
        )
        fila_sup.add_widget(cod_label)
        fila_sup.add_widget(estado_chip)

        desc_label = MDLabel(
            text=self.descripcion,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
        )

        columna.add_widget(fila_sup)
        columna.add_widget(desc_label)

        self.add_widget(barra)
        self.add_widget(columna)


class TarjetaModulo(TarjetaBase):
    """
    Tarjeta para mostrar un módulo ECU en el escaneo de capacidades.
    Muestra nombre, nivel de acceso (con color) y badges de capacidades.
    """
    nombre = StringProperty("ECU")
    descripcion = StringProperty("")
    nivel = NumericProperty(0)            # 0-4
    num_dtcs = NumericProperty(0)
    presente = BooleanProperty(True)

    COLORES_NIVEL = {
        0: Color.TEXTO_TENUE,
        1: Color.INFO,
        2: Color.CYAN,
        3: Color.PRIMARIO,
        4: Color.EXITO,
    }
    NOMBRES_NIVEL = {
        0: "Sin acceso",
        1: "OBD-II básico",
        2: "UDS básico",
        3: "UDS extendido",
        4: "Acceso completo",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(Dim.ESPACIO)
        self.size_hint_y = None
        self.height = dp(92)
        self._construir()

    def _construir(self):
        from kivymd.uix.label import MDIcon
        color_nivel = self.COLORES_NIVEL.get(self.nivel, Color.TEXTO_TENUE)

        # Ícono de estado del módulo
        cont_icono = MDCard(
            md_bg_color=(color_nivel[0], color_nivel[1], color_nivel[2], 0.15),
            radius=[dp(Dim.RADIO_CHICO)],
            size_hint=(None, None),
            size=(dp(52), dp(52)),
            pos_hint={"center_y": 0.5},
            elevation=0,
        )
        cont_icono.add_widget(MDIcon(
            icon="chip" if self.presente else "chip",
            theme_text_color="Custom",
            text_color=color_nivel,
            font_size=dp(28),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        ))

        # Columna de información
        columna = MDBoxLayout(orientation="vertical", spacing=dp(2),
                              pos_hint={"center_y": 0.5})
        columna.add_widget(MDLabel(
            text=self.nombre,
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_size=Fuente.SUBTITULO,
            bold=True,
            size_hint_y=None,
            height=dp(24),
        ))
        columna.add_widget(MDLabel(
            text=self.descripcion,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            size_hint_y=None,
            height=dp(18),
        ))
        columna.add_widget(MDLabel(
            text=f"◆ {self.NOMBRES_NIVEL.get(self.nivel, '')}",
            theme_text_color="Custom",
            text_color=color_nivel,
            font_size=Fuente.ETIQUETA,
            bold=True,
            size_hint_y=None,
            height=dp(16),
        ))

        # Badge de DTCs a la derecha
        col_dtc = MDBoxLayout(orientation="vertical", size_hint_x=None,
                              width=dp(56), pos_hint={"center_y": 0.5})
        if self.num_dtcs > 0:
            col_dtc.add_widget(MDLabel(
                text=str(self.num_dtcs),
                theme_text_color="Custom",
                text_color=Color.PELIGRO,
                font_size=Fuente.TITULO,
                bold=True,
                halign="center",
            ))
            col_dtc.add_widget(MDLabel(
                text="DTCs",
                theme_text_color="Custom",
                text_color=Color.TEXTO_SUAVE,
                font_size=Fuente.ETIQUETA,
                halign="center",
            ))
        elif self.presente:
            col_dtc.add_widget(MDIcon(
                icon="check-circle",
                theme_text_color="Custom",
                text_color=Color.EXITO,
                font_size=dp(24),
                halign="center",
            ))

        self.add_widget(cont_icono)
        self.add_widget(columna)
        self.add_widget(col_dtc)
