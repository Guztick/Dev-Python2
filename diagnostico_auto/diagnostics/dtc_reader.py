# -*- coding: utf-8 -*-
"""
Lector de DTCs — Diagnostic Trouble Codes.

Lee, clasifica, describe y permite borrar códigos de falla de
todos los módulos ECU del vehículo, en español.

Un DTC tiene:
  - Código: P0300, B0100, C0035, U0100, etc.
  - Estado: activo, histórico, pendiente, permanente
  - Descripción: qué significa el código
  - Freeze frame: qué valores tenía el motor cuando ocurrió el fallo
"""
import json
import os
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from core.hardware.elm327 import ELM327
from core.protocols.obd2 import OBD2
from core.protocols.uds import UDS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estados de DTC según byte de estado UDS (ISO 14229-1 Tabla D.1)
# ---------------------------------------------------------------------------
ESTADOS_DTC = {
    0x01: "Fallo activo",
    0x02: "Fallo pendiente",
    0x04: "Fallo confirmado",
    0x08: "Test no completado desde último borrado",
    0x10: "Test fallado desde último borrado",
    0x20: "Test fallado en operación actual",
    0x40: "Indicador de advertencia solicitado",
    0x80: "Fallo en ciclo de conducción anterior",
}


def _interpretar_estado(byte_estado: int) -> List[str]:
    """Traduce el byte de estado UDS a lista de descripciones legibles."""
    return [desc for bit, desc in ESTADOS_DTC.items() if byte_estado & bit]


@dataclass
class DTC:
    """Un código de falla diagnóstica con toda su información."""
    codigo: str                    # Ej: "P0300"
    descripcion: str               # En español
    estado_byte: int = 0           # Byte de estado UDS raw
    estados: List[str] = None      # Lista de estados interpretados
    fuente: str = "OBD-II"         # "OBD-II" o nombre del módulo
    freeze_frame: Dict = None      # Datos al momento del fallo

    def __post_init__(self):
        if self.estados is None:
            self.estados = _interpretar_estado(self.estado_byte)
        if self.freeze_frame is None:
            self.freeze_frame = {}

    @property
    def es_activo(self) -> bool:
        return bool(self.estado_byte & 0x01) or self.estado_byte == 0

    @property
    def tipo(self) -> str:
        tipos = {
            "P": "Motor/Transmisión (Powertrain)",
            "B": "Carrocería (Body)",
            "C": "Chasis (Chassis)",
            "U": "Red de comunicación (Network)",
        }
        return tipos.get(self.codigo[0], "Desconocido")

    def __str__(self) -> str:
        estado = "ACTIVO" if self.es_activo else "HISTÓRICO"
        return f"[{estado}] {self.codigo} — {self.descripcion}"


# ---------------------------------------------------------------------------
# Base de datos de descripciones en español
# ---------------------------------------------------------------------------

class BaseDTCs:
    """Carga y consulta la base de datos de descripciones de DTCs en español."""

    _instancia = None
    _datos: Dict[str, str] = {}

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._cargar()
        return cls._instancia

    def _cargar(self) -> None:
        ruta = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "database", "dtc_es.json"
        )
        try:
            with open(ruta, encoding="utf-8") as f:
                self._datos = json.load(f)
            logger.info(f"Base de DTCs cargada: {len(self._datos)} códigos")
        except FileNotFoundError:
            logger.warning("Base de DTCs no encontrada — se usarán descripciones genéricas")
            self._datos = {}

    def describir(self, codigo: str) -> str:
        """Retorna descripción en español del DTC, o texto genérico si no existe."""
        # Buscar exacto primero
        if codigo in self._datos:
            return self._datos[codigo]
        # Buscar sin número de fabricante (ej. P1xxx → descripción genérica de P1)
        return self._datos.get(codigo[:2] + "XXX", f"Fallo en {_area_codigo(codigo)}")


def _area_codigo(codigo: str) -> str:
    """Descripción del área del código basada en el prefijo."""
    areas = {
        "P0": "sistemas de motor y emisiones (genérico SAE)",
        "P1": "motor o transmisión (específico del fabricante)",
        "P2": "motor o transmisión (específico del fabricante)",
        "P3": "encendido o pérdida de potencia",
        "B0": "dispositivos de ocupante/carrocería",
        "B1": "sistemas de carrocería (específico)",
        "C0": "sistemas de frenos y suspensión",
        "C1": "chasis (específico del fabricante)",
        "U0": "red de comunicación CAN (genérico)",
        "U1": "red de comunicación (específico)",
    }
    return areas.get(codigo[:2], "sistema automotriz")


# ---------------------------------------------------------------------------
# Lector de DTCs
# ---------------------------------------------------------------------------

class LectorDTCs:
    """
    Lee DTCs de todos los módulos del vehículo usando OBD-II y/o UDS.
    Combina los resultados en una lista unificada con descripciones en español.
    """

    def __init__(self, adaptador: ELM327):
        self._elm = adaptador
        self._base = BaseDTCs()

    def leer_obd2(self) -> List[DTC]:
        """Lee DTCs estándar OBD-II (motor principal) — funciona en TODOS los vehículos."""
        obd = OBD2(self._elm)
        dtcs_raw = obd.leer_dtcs()
        dtcs_pendientes = obd.leer_dtcs_pendientes()
        dtcs_permanentes = obd.leer_dtcs_permanentes()

        resultados = []

        for codigo in dtcs_raw:
            resultados.append(DTC(
                codigo=codigo,
                descripcion=self._base.describir(codigo),
                estado_byte=0x05,  # Activo + confirmado
                fuente="OBD-II Motor",
            ))

        for codigo in dtcs_pendientes:
            if codigo not in dtcs_raw:
                resultados.append(DTC(
                    codigo=codigo,
                    descripcion=self._base.describir(codigo),
                    estado_byte=0x02,  # Pendiente
                    fuente="OBD-II Pendiente",
                ))

        for codigo in dtcs_permanentes:
            resultados.append(DTC(
                codigo=codigo,
                descripcion=self._base.describir(codigo),
                estado_byte=0x04,  # Confirmado permanente
                fuente="OBD-II Permanente",
            ))

        return resultados

    def leer_modulo_uds(self, id_solicitud: int, id_respuesta: int,
                        nombre_modulo: str) -> List[DTC]:
        """Lee DTCs de un módulo específico usando UDS (acceso avanzado)."""
        uds = UDS(self._elm, id_solicitud, id_respuesta)

        # Intentar sesión extendida para más datos
        uds.abrir_sesion_extendida()

        dtcs_raw = uds.leer_dtcs()
        uds.abrir_sesion_default()

        resultados = []
        for codigo, estado_byte in dtcs_raw:
            resultados.append(DTC(
                codigo=codigo,
                descripcion=self._base.describir(codigo),
                estado_byte=estado_byte,
                fuente=nombre_modulo,
            ))
        return resultados

    def leer_todos(self, modulos: List) -> Dict[str, List[DTC]]:
        """
        Lee DTCs de todos los módulos proporcionados.
        Retorna dict {nombre_modulo: [lista de DTCs]}.
        """
        resultados = {}

        # OBD-II estándar (siempre primero)
        dtcs_obd = self.leer_obd2()
        if dtcs_obd:
            resultados["Motor (OBD-II)"] = dtcs_obd

        # Módulos UDS
        for modulo in modulos:
            if modulo.id_solicitud == 0x7DF:
                continue  # La dirección funcional ya la cubrimos con OBD-II
            try:
                dtcs = self.leer_modulo_uds(
                    modulo.id_solicitud,
                    modulo.id_respuesta,
                    modulo.nombre,
                )
                if dtcs:
                    resultados[modulo.nombre] = dtcs
            except Exception as e:
                logger.debug(f"Error leyendo {modulo.nombre}: {e}")

        return resultados

    def limpiar_todos(self, modulos: List) -> Dict[str, bool]:
        """Borra DTCs de todos los módulos. Retorna dict {módulo: éxito}."""
        resultados = {}

        # Limpiar por OBD-II (motor)
        obd = OBD2(self._elm)
        resultados["Motor (OBD-II)"] = obd.limpiar_dtcs()

        # Limpiar por UDS en cada módulo
        for modulo in modulos:
            if modulo.id_solicitud == 0x7DF:
                continue
            try:
                uds = UDS(self._elm, modulo.id_solicitud, modulo.id_respuesta)
                uds.abrir_sesion_extendida()
                exito = uds.limpiar_dtcs()
                uds.abrir_sesion_default()
                resultados[modulo.nombre] = exito
            except Exception as e:
                logger.debug(f"Error borrando DTCs de {modulo.nombre}: {e}")
                resultados[modulo.nombre] = False

        return resultados

    def leer_freeze_frame(self, modulo_id: int = 0x7E0) -> Dict:
        """
        Lee el freeze frame del motor — los valores exactos del momento del fallo.
        Disponible en OBD-II Mode 02.
        """
        freeze = {}
        # OBD-II Mode 02 — freeze frame del motor
        resp = self._elm.enviar_obd(0x02, 0x00)
        if resp:
            freeze["obd2_disponible"] = True
            # Aquí se leerían los PIDs del freeze frame
        return freeze

    @staticmethod
    def formatear_reporte(dtcs_por_modulo: Dict[str, List[DTC]]) -> str:
        """Genera un reporte de texto con todos los DTCs encontrados."""
        if not dtcs_por_modulo:
            return "✅ No se encontraron códigos de falla en ningún módulo."

        total = sum(len(dtcs) for dtcs in dtcs_por_modulo.values())
        lineas = [
            f"\n{'═' * 60}",
            f"  REPORTE DE CÓDIGOS DE FALLA — {total} DTC(s) encontrado(s)",
            f"{'═' * 60}",
        ]

        for modulo, dtcs in dtcs_por_modulo.items():
            lineas.append(f"\n  📦 Módulo: {modulo} ({len(dtcs)} código(s))")
            lineas.append("  " + "─" * 55)
            for dtc in dtcs:
                estado = "⚠️ ACTIVO" if dtc.es_activo else "📋 HISTORIAL"
                lineas.append(f"  {estado}  {dtc.codigo}")
                lineas.append(f"            {dtc.descripcion}")
                if dtc.estados:
                    lineas.append(f"            Estado: {', '.join(dtc.estados[:2])}")

        lineas.append(f"\n{'═' * 60}")
        return "\n".join(lineas)
