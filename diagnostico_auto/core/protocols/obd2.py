# -*- coding: utf-8 -*-
"""
Protocolo OBD-II estándar (SAE J1979 / ISO 15031-5).

Implementa los 10 modos estándar de diagnóstico presentes en todos
los vehículos desde 1996 (EE.UU.) y 2001 (Europa).

Modos:
  01 — Datos actuales (live data / PIDs en tiempo real)
  02 — Datos de freeze frame (snapshot cuando ocurrió el DTC)
  03 — DTCs almacenados (códigos de error activos)
  04 — Limpiar DTCs e información de diagnóstico
  05 — Resultados de prueba sensores O2 (solo protocolo no-CAN)
  06 — Resultados de prueba on-board para sistemas específicos
  07 — DTCs pendientes (presentes pero no confirmados)
  08 — Control de sistema on-board (actuadores)
  09 — Información del vehículo (VIN, calibración ECU)
  0A — DTCs permanentes (no se borran con modo 04)
"""
import logging
from typing import Optional, List, Tuple, Dict
from ..hardware.elm327 import ELM327

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PIDs estándar Modo 01 con fórmulas de conversión
# ---------------------------------------------------------------------------
class PID:
    """Definición de un PID OBD-II estándar."""
    def __init__(self, numero: int, nombre: str, unidad: str,
                 bytes_datos: int, formula, descripcion: str = ""):
        self.numero = numero
        self.nombre = nombre
        self.unidad = unidad
        self.bytes_datos = bytes_datos
        self.formula = formula  # callable(bytes) -> valor numérico
        self.descripcion = descripcion

    def decodificar(self, datos: bytes) -> Optional[float]:
        try:
            return self.formula(datos)
        except Exception:
            return None


# Tabla de PIDs estándar Modo 01
PIDS_ESTANDAR: Dict[int, PID] = {
    0x04: PID(0x04, "Carga calculada motor", "%", 1,
              lambda d: d[0] * 100.0 / 255.0),
    0x05: PID(0x05, "Temperatura refrigerante", "°C", 1,
              lambda d: d[0] - 40),
    0x06: PID(0x06, "Corrección combustible a corto plazo - Banco 1", "%", 1,
              lambda d: (d[0] - 128) * 100.0 / 128.0),
    0x07: PID(0x07, "Corrección combustible a largo plazo - Banco 1", "%", 1,
              lambda d: (d[0] - 128) * 100.0 / 128.0),
    0x0B: PID(0x0B, "Presión absoluta del colector", "kPa", 1,
              lambda d: d[0]),
    0x0C: PID(0x0C, "RPM motor", "rpm", 2,
              lambda d: ((d[0] * 256) + d[1]) / 4.0),
    0x0D: PID(0x0D, "Velocidad del vehículo", "km/h", 1,
              lambda d: d[0]),
    0x0E: PID(0x0E, "Avance de encendido", "°", 1,
              lambda d: (d[0] / 2.0) - 64.0),
    0x0F: PID(0x0F, "Temperatura de aire de admisión", "°C", 1,
              lambda d: d[0] - 40),
    0x10: PID(0x10, "Flujo de aire (MAF)", "g/s", 2,
              lambda d: ((d[0] * 256) + d[1]) / 100.0),
    0x11: PID(0x11, "Posición del acelerador", "%", 1,
              lambda d: d[0] * 100.0 / 255.0),
    0x1F: PID(0x1F, "Tiempo desde encendido motor", "s", 2,
              lambda d: (d[0] * 256) + d[1]),
    0x21: PID(0x21, "Distancia con MIL encendida", "km", 2,
              lambda d: (d[0] * 256) + d[1]),
    0x2F: PID(0x2F, "Nivel de combustible", "%", 1,
              lambda d: d[0] * 100.0 / 255.0),
    0x31: PID(0x31, "Distancia desde limpieza DTCs", "km", 2,
              lambda d: (d[0] * 256) + d[1]),
    0x33: PID(0x33, "Presión atmosférica", "kPa", 1,
              lambda d: d[0]),
    0x42: PID(0x42, "Voltaje módulo de control", "V", 2,
              lambda d: ((d[0] * 256) + d[1]) / 1000.0),
    0x43: PID(0x43, "Carga absoluta del motor", "%", 2,
              lambda d: ((d[0] * 256) + d[1]) * 100.0 / 255.0),
    0x46: PID(0x46, "Temperatura ambiente", "°C", 1,
              lambda d: d[0] - 40),
    0x49: PID(0x49, "Posición acelerador acelerada", "%", 1,
              lambda d: d[0] * 100.0 / 255.0),
    0x4C: PID(0x4C, "Posición acelerador comandada", "%", 1,
              lambda d: d[0] * 100.0 / 255.0),
    0x5C: PID(0x5C, "Temperatura aceite motor", "°C", 1,
              lambda d: d[0] - 40),
    0x5E: PID(0x5E, "Tasa de flujo de combustible", "L/h", 2,
              lambda d: ((d[0] * 256) + d[1]) * 0.05),
    0x61: PID(0x61, "Torque de fricción solicitado", "%", 1,
              lambda d: d[0] - 125),
    0x62: PID(0x62, "Torque actual del motor", "%", 1,
              lambda d: d[0] - 125),
    0x63: PID(0x63, "Torque máximo de referencia", "Nm", 2,
              lambda d: (d[0] * 256) + d[1]),
}


class OBD2:
    """
    Protocolo OBD-II estándar — funciona en cualquier vehículo 1996+.

    Es el nivel base de diagnóstico. No requiere contraseñas ni acceso
    especial. Proporciona datos de motor, DTCs, y información del vehículo.
    """

    def __init__(self, adaptador: ELM327):
        self._elm = adaptador

    # ------------------------------------------------------------------
    # Modo 09 — Información del vehículo
    # ------------------------------------------------------------------

    def leer_vin(self) -> Optional[str]:
        """Lee el VIN (Número de Identificación del Vehículo) del ECU."""
        datos = self._elm.enviar_obd(0x09, 0x02, timeout=3.0)
        if not datos:
            return None
        try:
            # Los bytes del VIN comienzan después del byte de count (posición 1)
            vin_bytes = datos[1:] if datos[0] < 0x20 else datos
            return vin_bytes.decode("ascii", errors="ignore").strip("\x00").strip()
        except Exception:
            return None

    def leer_pids_soportados(self, grupo: int = 0x00) -> List[int]:
        """
        Lee qué PIDs soporta el vehículo en el grupo especificado.
        grupos: 0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0, 0xE0
        """
        datos = self._elm.enviar_obd(0x01, grupo)
        if not datos or len(datos) < 4:
            return []

        bitmap = (datos[0] << 24) | (datos[1] << 16) | (datos[2] << 8) | datos[3]
        pids = []
        for bit in range(32):
            if bitmap & (1 << (31 - bit)):
                pids.append(grupo + bit + 1)
        return pids

    # ------------------------------------------------------------------
    # Modo 01 — Datos en tiempo real
    # ------------------------------------------------------------------

    def leer_pid(self, pid: int) -> Optional[Tuple[float, str, str]]:
        """
        Lee un PID en tiempo real.
        Retorna (valor, unidad, nombre) o None si no está disponible.
        """
        if pid not in PIDS_ESTANDAR:
            return None

        definicion = PIDS_ESTANDAR[pid]
        datos = self._elm.enviar_obd(0x01, pid)
        if not datos:
            return None

        valor = definicion.decodificar(datos)
        if valor is None:
            return None
        return (valor, definicion.unidad, definicion.nombre)

    def leer_todos_los_pids(self) -> Dict[str, Tuple[float, str]]:
        """Lee todos los PIDs soportados. Retorna dict {nombre: (valor, unidad)}."""
        pids_disponibles = []
        for grupo in range(0, 0xE1, 0x20):
            pids_disponibles.extend(self.leer_pids_soportados(grupo))

        resultados = {}
        for pid in pids_disponibles:
            resultado = self.leer_pid(pid)
            if resultado:
                valor, unidad, nombre = resultado
                resultados[nombre] = (valor, unidad)
        return resultados

    # ------------------------------------------------------------------
    # Modo 03 — DTCs almacenados
    # ------------------------------------------------------------------

    def leer_dtcs(self) -> List[str]:
        """
        Lee los DTCs almacenados (códigos de falla activos).
        Retorna lista de strings en formato estándar (ej. ['P0300', 'P0115']).
        """
        datos = self._elm.enviar_obd(0x03, 0x00)
        if not datos:
            return []
        return self._decodificar_dtcs(datos)

    def leer_dtcs_pendientes(self) -> List[str]:
        """Lee DTCs pendientes (Modo 07) — fallos detectados pero no confirmados."""
        datos = self._elm.enviar_obd(0x07, 0x00)
        if not datos:
            return []
        return self._decodificar_dtcs(datos)

    def leer_dtcs_permanentes(self) -> List[str]:
        """Lee DTCs permanentes (Modo 0A) — no se borran con Modo 04."""
        datos = self._elm.enviar_obd(0x0A, 0x00)
        if not datos:
            return []
        return self._decodificar_dtcs(datos)

    def limpiar_dtcs(self) -> bool:
        """Borra todos los DTCs y apaga el MIL (Check Engine). ¡Irreversible!"""
        resp = self._elm._conn.enviar_recibir("04", timeout=5.0)
        return "44" in resp or "OK" in resp

    @staticmethod
    def _decodificar_dtcs(datos: bytes) -> List[str]:
        """Convierte bytes en formato OBD-II a códigos DTC legibles."""
        dtcs = []
        i = 0
        while i + 1 < len(datos):
            byte_alto = datos[i]
            byte_bajo = datos[i + 1]
            if byte_alto == 0 and byte_bajo == 0:
                i += 2
                continue

            tipo = (byte_alto >> 6) & 0x03
            prefijo = ["P", "C", "B", "U"][tipo]
            numero = ((byte_alto & 0x3F) << 8) | byte_bajo
            dtc = f"{prefijo}{numero:04X}"
            dtcs.append(dtc)
            i += 2
        return dtcs

    # ------------------------------------------------------------------
    # Modo 01 PID 01 — Estado del monitor / MIL
    # ------------------------------------------------------------------

    def leer_estado_monitor(self) -> Dict:
        """
        Lee el estado del MIL (Check Engine), número de DTCs, y
        estado de los monitores de emisión.
        """
        datos = self._elm.enviar_obd(0x01, 0x01)
        if not datos or len(datos) < 4:
            return {}

        mil_encendido = bool(datos[0] & 0x80)
        num_dtcs = datos[0] & 0x7F

        return {
            "mil_encendido": mil_encendido,
            "num_dtcs": num_dtcs,
            "motor_diesel": bool(datos[1] & 0x08),
            "monitores_listos": {
                "misfire": not bool(datos[1] & 0x10),
                "fuel_system": not bool(datos[1] & 0x20),
                "components": not bool(datos[1] & 0x40),
                "catalyst": not bool(datos[2] & 0x01),
                "heated_catalyst": not bool(datos[2] & 0x02),
                "evap_system": not bool(datos[2] & 0x04),
                "sec_air_system": not bool(datos[2] & 0x08),
                "ac_refrigerant": not bool(datos[2] & 0x10),
                "o2_sensor": not bool(datos[2] & 0x20),
                "o2_sensor_heater": not bool(datos[2] & 0x40),
                "egr_system": not bool(datos[2] & 0x80),
            },
        }
