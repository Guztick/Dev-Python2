# -*- coding: utf-8 -*-
"""
Detección de información y capacidades del adaptador (escáner).

Interroga al adaptador ELM327 conectado para determinar sus detalles
técnicos: versión, fabricante, si es genuino o clon, voltaje, y qué
protocolos de comunicación soporta.

Esto permite al usuario saber el alcance real de su escáner antes de
diagnosticar el vehículo.
"""
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from .base import ConexionBase
from .elm327 import PROTOCOLOS

logger = logging.getLogger(__name__)


@dataclass
class InfoAdaptador:
    """Información técnica completa del adaptador OBD-II."""
    identidad: str = ""                 # Respuesta a ATI (ej. "ELM327 v1.5")
    descripcion: str = ""              # Respuesta a AT@1
    identificador: str = ""           # Respuesta a AT@2
    version_elm: str = ""             # Versión extraída (ej. "1.5")
    fabricante_chip: str = "Desconocido"
    es_genuino: Optional[bool] = None  # True=genuino, False=clon, None=indeterminado
    voltaje: Optional[float] = None
    protocolos_soportados: List[str] = field(default_factory=list)
    protocolo_actual: Optional[str] = None
    tipo_conexion: str = ""           # WiFi / Bluetooth / USB

    def nivel_calidad(self) -> str:
        """Evalúa la calidad/alcance del adaptador."""
        if self.es_genuino:
            return "Genuino — alcance completo, máxima compatibilidad"
        if self.es_genuino is False:
            try:
                v = float(self.version_elm)
                if v >= 2.0:
                    return "Clon v2.x — buen alcance, compatible con la mayoría"
                if v >= 1.5:
                    return "Clon v1.5 — alcance estándar, suficiente para diagnóstico básico"
                return "Clon antiguo — alcance limitado"
            except ValueError:
                return "Clon — alcance variable"
        return "Indeterminado"

    def resumen(self) -> Dict[str, str]:
        """Retorna un diccionario legible con los datos clave."""
        return {
            "Identidad": self.identidad or "No disponible",
            "Versión ELM": self.version_elm or "No disponible",
            "Chip": self.fabricante_chip,
            "Autenticidad": (
                "Genuino ✓" if self.es_genuino else
                "Clon" if self.es_genuino is False else "Indeterminado"
            ),
            "Calidad": self.nivel_calidad(),
            "Voltaje leído": f"{self.voltaje:.1f} V" if self.voltaje else "N/D",
            "Protocolos": f"{len(self.protocolos_soportados)} soportados",
            "Conexión": self.tipo_conexion or "N/D",
        }


class DetectorAdaptador:
    """
    Interroga un adaptador ELM327 para extraer sus capacidades.

    Funciona directamente sobre la conexión (antes o después de la
    inicialización completa del ELM327).
    """

    def __init__(self, conexion: ConexionBase, tipo_conexion: str = ""):
        self._conn = conexion
        self._tipo = tipo_conexion

    def _at(self, cmd: str, timeout: float = 2.0) -> str:
        """Envía un comando AT y limpia la respuesta."""
        resp = self._conn.enviar_recibir(cmd, timeout=timeout)
        return resp.replace("\r", " ").replace("\n", " ").strip()

    def detectar(self) -> InfoAdaptador:
        """Ejecuta la secuencia completa de detección del adaptador."""
        info = InfoAdaptador(tipo_conexion=self._tipo)

        # Reset e inicialización mínima
        self._at("ATZ", timeout=2.0)
        time.sleep(1.0)
        self._at("ATE0")  # Echo off

        # ===== Identidad (ATI) =====
        info.identidad = self._limpiar_id(self._at("ATI"))
        info.version_elm = self._extraer_version(info.identidad)

        # ===== Descripción del dispositivo (AT@1) =====
        info.descripcion = self._limpiar_id(self._at("AT@1"))

        # ===== Identificador del dispositivo (AT@2) =====
        info.identificador = self._limpiar_id(self._at("AT@2"))

        # ===== Detectar fabricante del chip =====
        info.fabricante_chip = self._detectar_chip(info)

        # ===== Detectar si es genuino o clon =====
        info.es_genuino = self._es_genuino(info)

        # ===== Voltaje =====
        info.voltaje = self._leer_voltaje()

        # ===== Protocolo actual =====
        dpn = self._at("ATDPN")
        if dpn:
            num = dpn.replace("A", "").strip()
            info.protocolo_actual = PROTOCOLOS.get(num[-1] if num else "0")

        # ===== Protocolos soportados =====
        info.protocolos_soportados = self._listar_protocolos()

        logger.info(f"Adaptador detectado: {info.identidad} ({info.fabricante_chip})")
        return info

    # ------------------------------------------------------------------
    # Helpers de parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _limpiar_id(texto: str) -> str:
        """Limpia respuestas de identidad de caracteres de control y prompts."""
        return texto.replace(">", "").replace("ATI", "").replace("AT@1", "") \
                    .replace("AT@2", "").strip()

    @staticmethod
    def _extraer_version(identidad: str) -> str:
        """Extrae el número de versión de la cadena de identidad."""
        # Ejemplos: "ELM327 v1.5", "ELM327 v2.1", "OBDII v1.5"
        import re
        match = re.search(r"v?(\d+\.\d+)", identidad, re.IGNORECASE)
        return match.group(1) if match else ""

    @staticmethod
    def _detectar_chip(info: InfoAdaptador) -> str:
        """Identifica el fabricante del chip según las respuestas."""
        texto = (info.identidad + " " + info.descripcion + " " +
                 info.identificador).upper()

        if "ELM327" in texto:
            # Distinguir entre genuino ELM (Canadá) y clones comunes
            if "OBDII TO RS232" in texto or "ELM ELECTRONICS" in texto:
                return "ELM Electronics (genuino)"
            return "ELM327 compatible (clon habitual)"
        if "STN" in texto or "OBDLINK" in texto or "SCANTOOL" in texto:
            return "OBDLink / STN (premium)"
        if "ICAR" in texto or "VGATE" in texto:
            return "Vgate iCar"
        if "KONNWEI" in texto:
            return "Konnwei"
        return "Desconocido / compatible"

    @staticmethod
    def _es_genuino(info: InfoAdaptador) -> Optional[bool]:
        """
        Heurística para detectar si el ELM327 es genuino o clon.

        Los ELM327 genuinos llegaron hasta la versión v1.4b oficialmente
        (v2.x son clones o chips mejorados de terceros como STN).
        La mayoría de adaptadores baratos reportan v1.5 o v2.1 y son clones.
        """
        texto = (info.identidad + " " + info.descripcion).upper()

        # OBDLink/STN son chips legítimos de terceros (no clones)
        if "STN" in texto or "OBDLINK" in texto:
            return True

        if "ELM ELECTRONICS" in texto:
            return True

        # v1.5 y v2.1 son las versiones clon más comunes
        # (ELM nunca lanzó oficialmente la v1.5)
        if info.version_elm in ("1.5", "2.1", "2.2", "2.3"):
            return False

        # v1.0 a v1.4 podrían ser genuinos
        try:
            v = float(info.version_elm)
            if v <= 1.4:
                return True
        except ValueError:
            pass

        return None  # No se puede determinar con certeza

    def _leer_voltaje(self) -> Optional[float]:
        resp = self._at("ATRV")
        try:
            return float(resp.replace("V", "").strip())
        except ValueError:
            return None

    def _listar_protocolos(self) -> List[str]:
        """
        Prueba qué protocolos puede usar el adaptador.

        Todos los ELM327 soportan los protocolos del 1 al A en hardware;
        aquí los listamos como capacidades del adaptador (no del vehículo).
        """
        # Los protocolos 1-9 y A están soportados por hardware en todo ELM327.
        # Los clones modernos (v1.5/v2.1) soportan toda la gama.
        soportados = []
        for codigo, nombre in PROTOCOLOS.items():
            if codigo == "0":  # "Auto" no es un protocolo físico
                continue
            soportados.append(nombre)
        return soportados
