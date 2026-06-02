# -*- coding: utf-8 -*-
"""
Sistema de diseño de DiagnosticoPro.

Define la paleta de colores, dimensiones, tipografía y estilos
para una apariencia profesional consistente en toda la app.

Filosofía: tema oscuro automotriz, alto contraste para legibilidad
en condiciones de taller (luz variable), acentos de color por severidad.
"""
from kivy.utils import get_color_from_hex as hexcolor


class Color:
    """Paleta de colores de la aplicación (formato RGBA normalizado)."""

    # ===== Fondos =====
    FONDO          = hexcolor("#0D1117")   # Fondo principal (casi negro azulado)
    FONDO_ELEVADO  = hexcolor("#161B22")   # Superficies elevadas
    SUPERFICIE     = hexcolor("#1C2128")   # Tarjetas y paneles
    SUPERFICIE_ALT = hexcolor("#22272E")   # Tarjetas resaltadas / hover

    # ===== Acentos primarios =====
    PRIMARIO       = hexcolor("#2F81F7")   # Azul de acción (botones, enlaces)
    PRIMARIO_OSC   = hexcolor("#1F6FEB")   # Azul presionado
    CYAN           = hexcolor("#39D0D8")   # Cyan técnico (datos, gauges)

    # ===== Estados / Severidad =====
    EXITO          = hexcolor("#3FB950")   # Verde — OK, conectado, sin fallos
    ADVERTENCIA    = hexcolor("#D29922")   # Ámbar — precaución, pendiente
    PELIGRO        = hexcolor("#F85149")   # Rojo — DTC activo, fallo crítico
    INFO           = hexcolor("#58A6FF")   # Azul claro — informativo

    # ===== Texto =====
    TEXTO          = hexcolor("#E6EDF3")   # Texto principal
    TEXTO_SUAVE    = hexcolor("#7D8590")   # Texto secundario
    TEXTO_TENUE    = hexcolor("#484F58")   # Texto deshabilitado / hints

    # ===== Bordes / Divisores =====
    BORDE          = hexcolor("#30363D")   # Bordes de tarjetas
    BORDE_ACTIVO   = hexcolor("#2F81F7")   # Borde resaltado

    # ===== Transparencias útiles =====
    TRANSPARENTE   = (0, 0, 0, 0)
    OVERLAY        = (0, 0, 0, 0.6)        # Capa modal


class Dim:
    """Dimensiones estándar en dp para consistencia."""
    RADIO          = 16        # Radio de esquinas de tarjetas
    RADIO_CHICO    = 10
    RADIO_GRANDE   = 24

    PADDING        = 16        # Padding estándar
    PADDING_CHICO  = 8
    PADDING_GRANDE = 24

    ESPACIO        = 12        # Espaciado entre elementos
    ESPACIO_CHICO  = 6

    ALTURA_BARRA   = 56        # Barra superior
    ALTURA_NAV     = 64        # Navegación inferior
    ALTURA_BOTON   = 48        # Botones de acción
    ALTURA_TARJETA = 88        # Tarjetas de stat

    ELEVACION      = 2         # Sombra de tarjetas


class Fuente:
    """Tamaños de tipografía en sp."""
    TITULO_XL      = "28sp"    # Títulos de pantalla
    TITULO         = "22sp"    # Encabezados de sección
    SUBTITULO      = "18sp"    # Subtítulos
    CUERPO         = "15sp"    # Texto normal
    SECUNDARIO     = "13sp"    # Texto pequeño
    ETIQUETA       = "11sp"    # Etiquetas / chips
    DATO_GRANDE    = "34sp"    # Valores grandes (gauges, stats)


# Tema KivyMD a aplicar en la App
TEMA_KIVYMD = {
    "theme_style": "Dark",
    "primary_palette": "Blue",
    "accent_palette": "Cyan",
    "material_style": "M3",
}
