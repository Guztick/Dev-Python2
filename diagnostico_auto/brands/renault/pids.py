# -*- coding: utf-8 -*-
"""
PIDs propietarios Renault (Data Identifiers - DIDs UDS 0x22).

Renault expone parámetros internos del motor y la transmisión
mediante el servicio UDS ReadDataByIdentifier (0x22) con DIDs
específicos de marca, adicionales a los estándar OBD-II.

Estos valores han sido documentados mediante ingeniería inversa
y referencia cruzada con herramientas de diagnóstico como
Clip, DDT2000 y documentación técnica de concesionario.
"""
from typing import NamedTuple, Dict, Callable, Optional


class PIDRenault(NamedTuple):
    did: int               # Data Identifier (2 bytes, UDS 0x22)
    nombre: str
    unidad: str
    formula: Callable      # Bytes crudos → valor en unidad
    bytes_respuesta: int   # Longitud esperada de respuesta en bytes
    descripcion: str = ""


def _signed_byte(data: bytes, idx: int = 0) -> float:
    """Byte con signo (complemento a dos)."""
    v = data[idx]
    return v - 256 if v > 127 else float(v)


def _u16_be(data: bytes, idx: int = 0) -> float:
    """Entero sin signo 16-bit big-endian."""
    return float((data[idx] << 8) | data[idx + 1])


def _s16_be(data: bytes, idx: int = 0) -> float:
    """Entero con signo 16-bit big-endian."""
    v = (data[idx] << 8) | data[idx + 1]
    return float(v - 65536) if v > 32767 else float(v)


# ---------------------------------------------------------------------------
# PIDs propietarios Renault — Motor UCE (solicitados a 0x7E0)
# ---------------------------------------------------------------------------
PIDS_MOTOR_RENAULT: Dict[int, PIDRenault] = {

    # ===== PARÁMETROS BÁSICOS DE MOTOR =====
    0x1000: PIDRenault(0x1000, "RPM motor (Renault)", "rpm", 2,
                       lambda d: _u16_be(d) * 0.25,
                       "Velocidad del motor en rpm — valor directo del ECU"),

    0x1001: PIDRenault(0x1001, "Temperatura refrigerante ECU", "°C", 1,
                       lambda d: data[0] - 40,
                       "Temperatura del refrigerante según el ECU (no sensor OBD)"),

    0x1002: PIDRenault(0x1002, "Temperatura aceite motor", "°C", 1,
                       lambda d: d[0] - 40,
                       "Temperatura aceite — clave para diagnóstico de lubricación"),

    0x1003: PIDRenault(0x1003, "Temperatura combustible", "°C", 1,
                       lambda d: d[0] - 40,
                       "Temperatura del combustible en riel/bomba"),

    0x1004: PIDRenault(0x1004, "Presión riel combustible", "MPa", 2,
                       lambda d: _u16_be(d) * 0.01,
                       "Presión en el riel de inyectores — crítico en diesel K9K"),

    0x1005: PIDRenault(0x1005, "Presión turbo boost", "hPa", 2,
                       lambda d: _u16_be(d) * 0.1,
                       "Presión de sobrealimentación del turbocompresor"),

    0x1006: PIDRenault(0x1006, "Caudal EGR", "%", 1,
                       lambda d: d[0] * 100.0 / 255.0,
                       "Porcentaje de apertura de la válvula EGR"),

    0x1007: PIDRenault(0x1007, "Posición EGR real", "%", 1,
                       lambda d: d[0] * 100.0 / 255.0,
                       "Posición actual (medida) de la válvula EGR"),

    0x1008: PIDRenault(0x1008, "Posición EGR objetivo", "%", 1,
                       lambda d: d[0] * 100.0 / 255.0,
                       "Posición deseada de la válvula EGR según el ECU"),

    0x1009: PIDRenault(0x1009, "Masa de aire aspirada", "kg/h", 2,
                       lambda d: _u16_be(d) * 0.1,
                       "Flujo másico de aire medido por el MAF"),

    0x100A: PIDRenault(0x100A, "Posición acelerador pedal", "%", 1,
                       lambda d: d[0] * 100.0 / 255.0,
                       "Posición del pedal del acelerador"),

    0x100B: PIDRenault(0x100B, "Carga motor", "%", 1,
                       lambda d: d[0] * 100.0 / 255.0,
                       "Carga calculada del motor"),

    0x100C: PIDRenault(0x100C, "Avance de inyección", "°BTDC", 1,
                       lambda d: _signed_byte(d) * 0.5,
                       "Avance del punto de inyección (diesel) o encendido (gasolina)"),

    # ===== DIESEL K9K (1.5 dCi) — Específico =====
    0x1010: PIDRenault(0x1010, "Cantidad inyección piloto", "mm³/ciclo", 2,
                       lambda d: _u16_be(d) * 0.01,
                       "Cantidad de combustible en inyección piloto (pre-inyección)"),

    0x1011: PIDRenault(0x1011, "Cantidad inyección principal", "mm³/ciclo", 2,
                       lambda d: _u16_be(d) * 0.01,
                       "Cantidad de combustible en inyección principal"),

    0x1012: PIDRenault(0x1012, "Duración inyección", "µs", 2,
                       lambda d: _u16_be(d),
                       "Duración del pulso de inyección en microsegundos"),

    0x1013: PIDRenault(0x1013, "Presión de admisión objetivo", "hPa", 2,
                       lambda d: _u16_be(d) * 0.1,
                       "Presión de turbo deseada por el ECU"),

    0x1014: PIDRenault(0x1014, "Posición VGT/turbo", "%", 1,
                       lambda d: d[0] * 100.0 / 255.0,
                       "Posición de la turbina de geometría variable"),

    0x1015: PIDRenault(0x1015, "Diferencial presión DPF", "mbar", 2,
                       lambda d: _s16_be(d) * 0.1,
                       "Diferencia de presión en el filtro de partículas (DPF)"),

    0x1016: PIDRenault(0x1016, "Temperatura DPF upstream", "°C", 2,
                       lambda d: _u16_be(d) - 40,
                       "Temperatura antes del DPF — clave para regeneración"),

    0x1017: PIDRenault(0x1017, "Temperatura DPF downstream", "°C", 2,
                       lambda d: _u16_be(d) - 40,
                       "Temperatura después del DPF"),

    0x1018: PIDRenault(0x1018, "Estado regeneración DPF", "enum", 1,
                       lambda d: float(d[0]),
                       "0=Inactivo 1=Activo 2=Inhibido 3=En espera"),

    # ===== GASOLINA (H4M/K4M) — Específico =====
    0x1020: PIDRenault(0x1020, "Corrección combustible B1 CT", "%", 1,
                       lambda d: (d[0] - 128) * 100.0 / 128.0,
                       "Corrección a corto plazo banco 1 (gasolina)"),

    0x1021: PIDRenault(0x1021, "Corrección combustible B1 LT", "%", 1,
                       lambda d: (d[0] - 128) * 100.0 / 128.0,
                       "Corrección a largo plazo banco 1 (gasolina)"),

    0x1022: PIDRenault(0x1022, "Lambda sensor O2 B1S1", "λ", 2,
                       lambda d: _u16_be(d) / 32768.0,
                       "Relación aire-combustible normalizada"),

    # ===== IDENTIFICACIÓN DE ECU =====
    0xF187: PIDRenault(0xF187, "Número de parte ECU", "texto", 10,
                       lambda d: d.decode("ascii", errors="ignore").strip("\x00"),
                       "Número de parte del módulo ECU"),

    0xF189: PIDRenault(0xF189, "Versión software ECU", "texto", 4,
                       lambda d: d.hex().upper(),
                       "Versión de calibración del software"),

    0xF190: PIDRenault(0xF190, "VIN", "texto", 17,
                       lambda d: d.decode("ascii", errors="ignore").strip("\x00"),
                       "Número de identificación del vehículo (17 caracteres)"),

    0xF18B: PIDRenault(0xF18B, "Fecha de fabricación ECU", "fecha", 3,
                       lambda d: f"{d[2]:02d}/{d[1]:02d}/20{d[0]:02d}",
                       "Fecha de fabricación del módulo (año/mes/día)"),

    0xF18C: PIDRenault(0xF18C, "Número de serie ECU", "hex", 10,
                       lambda d: d.hex().upper(),
                       "Número de serie único del hardware ECU"),
}


# ---------------------------------------------------------------------------
# PIDs de la caja de velocidades (TCM — 0x7E1)
# ---------------------------------------------------------------------------
PIDS_CAJA: Dict[int, PIDRenault] = {
    0x2000: PIDRenault(0x2000, "Temperatura aceite caja", "°C", 1,
                       lambda d: d[0] - 40,
                       "Temperatura del ATF en la transmisión automática/EDC"),

    0x2001: PIDRenault(0x2001, "Marcha engranada", "marcha", 1,
                       lambda d: float(d[0]),
                       "Marcha actual: 0=Neutral/Park, 1-7=marcha"),

    0x2002: PIDRenault(0x2002, "Marcha objetivo", "marcha", 1,
                       lambda d: float(d[0]),
                       "Marcha que el TCM está tratando de seleccionar"),

    0x2003: PIDRenault(0x2003, "Presión de embrague", "bar", 2,
                       lambda d: _u16_be(d) * 0.01,
                       "Presión del embrague (EDC/DSG)"),

    0x2004: PIDRenault(0x2004, "RPM embrague entrada", "rpm", 2,
                       lambda d: _u16_be(d) * 0.5,
                       "Velocidad del eje de entrada del embrague"),

    0x2005: PIDRenault(0x2005, "RPM embrague salida", "rpm", 2,
                       lambda d: _u16_be(d) * 0.5,
                       "Velocidad del eje de salida del embrague"),

    0x2006: PIDRenault(0x2006, "Modo de conducción", "enum", 1,
                       lambda d: float(d[0]),
                       "0=Normal 1=Sport 2=Eco 3=4WD"),

    0x2007: PIDRenault(0x2007, "Estado deslizamiento", "rpm", 2,
                       lambda d: _s16_be(d),
                       "Diferencia de RPM entrada-salida (slip del convertidor/embrague)"),
}
