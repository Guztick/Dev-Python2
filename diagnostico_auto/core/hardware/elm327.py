# -*- coding: utf-8 -*-
"""
Adaptador ELM327 — interfaz de alto nivel sobre cualquier conexión.

El ELM327 es el chip más común para acceder al bus OBD-II del vehículo.
Soporta todos los protocolos OBD-II y actúa como puente hacia CAN/ISO-TP/UDS.
"""
import time
import logging
from typing import Optional, List, Tuple
from .base import ConexionBase

logger = logging.getLogger(__name__)

# Protocolos soportados por el ELM327
PROTOCOLOS = {
    "0": "Auto",
    "1": "SAE J1850 PWM (41.6 kbps)",
    "2": "SAE J1850 VPW (10.4 kbps)",
    "3": "ISO 9141-2 (5 baud init, 10.4 kbps)",
    "4": "ISO 14230-4 KWP (5 baud init)",
    "5": "ISO 14230-4 KWP (fast init)",
    "6": "ISO 15765-4 CAN (11 bit ID, 500 kbps)",
    "7": "ISO 15765-4 CAN (29 bit ID, 500 kbps)",
    "8": "ISO 15765-4 CAN (11 bit ID, 250 kbps)",
    "9": "ISO 15765-4 CAN (29 bit ID, 250 kbps)",
    "A": "SAE J1939 CAN (29 bit ID, 250 kbps)",
}


class ELM327:
    """
    Adaptador ELM327 — capa de acceso al vehículo.

    Soporta tres tipos de operación:
    - Comandos AT (configuración del adaptador)
    - Comandos OBD-II estándar (modos 01-0A)
    - Comandos CAN raw con headers personalizados (para UDS/propietario)
    """

    def __init__(self, conexion: ConexionBase):
        self._conn = conexion
        self.protocolo_activo: Optional[str] = None
        self.version_elm: Optional[str] = None
        self._cabeceras_activas = False

    # ------------------------------------------------------------------
    # Conexión e inicialización
    # ------------------------------------------------------------------

    def conectar(self) -> bool:
        """Conecta y realiza la secuencia de inicialización del ELM327."""
        if not self._conn.conectar():
            logger.error("No se pudo establecer la conexión física.")
            return False

        time.sleep(0.5)

        # Secuencia de inicialización estándar
        self._at("ATZ")          # Reset completo
        time.sleep(1.2)
        self._at("ATE0")         # Echo OFF — no duplicar comandos en respuesta
        self._at("ATL0")         # Saltos de línea OFF
        self._at("ATS0")         # Espacios OFF (respuesta más compacta)
        self._at("ATH1")         # Headers ON — esencial para multi-ECU
        self._at("ATAT2")        # Timing adaptativo agresivo
        self._at("ATAL")         # Permitir mensajes largos (>7 bytes CAN)
        self._at("ATCAF1")       # CAN auto-format ON (ELM327 maneja ISO-TP)

        self._cabeceras_activas = True

        version = self._at("ATI")
        self.version_elm = version
        logger.info(f"ELM327 inicializado: {version}")

        protocolo = self._at("ATDP")
        self.protocolo_activo = protocolo
        logger.info(f"Protocolo activo: {protocolo}")

        return True

    def desconectar(self) -> None:
        self._at("ATPC")  # Protocolo cerrado
        self._conn.desconectar()
        logger.info("ELM327 desconectado.")

    # ------------------------------------------------------------------
    # API interna
    # ------------------------------------------------------------------

    def _at(self, cmd: str, timeout: float = 2.0) -> str:
        """Envía un comando AT y retorna la respuesta limpia."""
        resp = self._conn.enviar_recibir(cmd, timeout=timeout)
        resp = resp.replace("\r", "").replace("\n", "").strip()
        logger.debug(f"AT >> {cmd}  << {resp}")
        return resp

    def seleccionar_protocolo(self, protocolo: str = "0") -> bool:
        """
        Selecciona protocolo CAN/OBD.
        '0' = auto-detectar (recomendado para primer uso).
        '6' = CAN 11-bit 500kbps (Renault Duster, GM, Ford modernos).
        '8' = CAN 11-bit 250kbps (algunos GM/Ford).
        """
        resp = self._at(f"ATSP{protocolo}")
        return "OK" in resp

    # ------------------------------------------------------------------
    # OBD-II estándar (Modos 01–0A)
    # ------------------------------------------------------------------

    def enviar_obd(self, modo: int, pid: int, longitud_esperada: int = 0) -> Optional[bytes]:
        """
        Envía un comando OBD-II estándar al bus (dirección funcional 0x7DF).
        Retorna los bytes de datos de la respuesta, o None en error.
        """
        if longitud_esperada > 0:
            # Solicitar número exacto de respuestas (evita timeouts innecesarios)
            cmd = f"{modo:02X}{pid:02X}{longitud_esperada:02X}"
        else:
            cmd = f"{modo:02X}{pid:02X}"

        resp = self._conn.enviar_recibir(cmd, timeout=2.0)
        return self._parsear_respuesta_obd(resp, modo)

    def _parsear_respuesta_obd(self, respuesta: str, modo: int) -> Optional[bytes]:
        """Extrae los bytes de datos de una respuesta OBD-II."""
        if not respuesta or "NO DATA" in respuesta or "ERROR" in respuesta:
            return None

        lineas = [l.strip() for l in respuesta.split("\n") if l.strip()]
        for linea in lineas:
            # Quitar dirección de respuesta (header) si está presente
            # Formato con header: "7E8 06 41 0C xx xx xx xx"
            partes = linea.split()
            try:
                # El byte de respuesta es modo + 0x40
                byte_respuesta = modo + 0x40
                if len(partes) >= 3:
                    # Buscar el byte de respuesta en la línea
                    for i, p in enumerate(partes):
                        if int(p, 16) == byte_respuesta and i + 1 < len(partes):
                            # Los datos empiezan después del modo y PID
                            datos_hex = partes[i + 2:]
                            return bytes(int(b, 16) for b in datos_hex)
                # Formato sin header
                if int(partes[0], 16) == byte_respuesta and len(partes) >= 2:
                    return bytes(int(b, 16) for b in partes[2:])
            except (ValueError, IndexError):
                continue
        return None

    # ------------------------------------------------------------------
    # UDS / Propietario (CAN con header personalizado)
    # ------------------------------------------------------------------

    def establecer_header(self, can_id: int) -> bool:
        """
        Establece el CAN ID de destino para los siguientes comandos.
        Para UDS 11-bit: can_id = 0x7E0 (motor Renault), 0x7C0 (ABS), etc.
        """
        resp = self._at(f"ATSH{can_id:03X}")
        return "OK" in resp

    def establecer_filtro_respuesta(self, can_id: int) -> bool:
        """Filtra para recibir solo respuestas del ECU especificado."""
        resp = self._at(f"ATCRA{can_id:03X}")
        return "OK" in resp

    def configurar_control_flujo(self, header_id: int) -> bool:
        """
        Configura ISO-TP flow control para mensajes multi-frame.
        Necesario para respuestas UDS largas (DTCs, listas de PIDs, etc.).
        """
        self._at(f"ATFCSH{header_id:03X}")
        self._at("ATFCSM1")   # Modo 1: ELM327 maneja FC automáticamente
        self._at("ATFCSD300000")  # BS=0x30, ST=0x00, len=0x00
        return True

    def enviar_uds(
        self,
        id_destino: int,
        id_respuesta: int,
        servicio: int,
        datos: bytes = b"",
        timeout: float = 3.0,
    ) -> Optional[bytes]:
        """
        Envía un frame UDS al ECU especificado y retorna la respuesta.

        Parámetros:
            id_destino:  CAN ID del ECU (ej. 0x7E0 para motor Renault)
            id_respuesta: CAN ID de respuesta esperada (ej. 0x7E8)
            servicio:    Código de servicio UDS (ej. 0x19 para leer DTCs)
            datos:       Bytes adicionales del request
        """
        self.establecer_header(id_destino)
        self.establecer_filtro_respuesta(id_respuesta)
        self.configurar_control_flujo(id_destino + 8)  # FC header = req + 8

        payload = bytes([servicio]) + datos
        hex_cmd = " ".join(f"{b:02X}" for b in payload)

        resp = self._conn.enviar_recibir(hex_cmd, timeout=timeout)
        return self._parsear_respuesta_uds(resp, servicio)

    def _parsear_respuesta_uds(self, respuesta: str, servicio: int) -> Optional[bytes]:
        """Extrae datos de una respuesta UDS."""
        if not respuesta or "NO DATA" in respuesta or "TIMEOUT" in respuesta:
            return None

        lineas = [l.strip() for l in respuesta.split("\n") if l.strip()]
        datos_completos = []

        for linea in lineas:
            partes = linea.split()
            try:
                # Saltar header CAN (3 chars hex) si está presente
                inicio = 0
                if len(partes[0]) == 3:  # header como "7E8"
                    inicio = 1
                # Saltar byte de longitud ISO-TP (ej. "06")
                inicio += 1
                datos_completos.extend(int(p, 16) for p in partes[inicio:])
            except (ValueError, IndexError):
                continue

        if not datos_completos:
            return None

        # Verificar si es respuesta positiva (servicio + 0x40) o negativa (0x7F)
        if datos_completos[0] == 0x7F:
            codigo_nrc = datos_completos[2] if len(datos_completos) > 2 else 0
            logger.warning(f"UDS respuesta negativa NRC=0x{codigo_nrc:02X}: {_nrc_descripcion(codigo_nrc)}")
            return None

        return bytes(datos_completos)

    # ------------------------------------------------------------------
    # Escaneo de protocolos disponibles
    # ------------------------------------------------------------------

    def detectar_protocolo_vehiculo(self) -> Optional[str]:
        """
        Intenta conectar al vehículo con auto-detección de protocolo.
        Retorna el protocolo detectado o None si no hay comunicación.
        """
        self._at("ATSP0")  # Auto
        resp = self._conn.enviar_recibir("0100", timeout=5.0)  # OBD Mode 01 PID 00

        if "NO DATA" in resp or "UNABLE" in resp or not resp:
            return None

        protocolo = self._at("ATDP")
        self.protocolo_activo = protocolo
        return protocolo

    def leer_voltage_bateria(self) -> Optional[float]:
        """Retorna el voltaje de la batería del vehículo (útil para diagnóstico)."""
        resp = self._at("ATRV")
        try:
            return float(resp.replace("V", "").strip())
        except ValueError:
            return None


def _nrc_descripcion(codigo: int) -> str:
    """Descripción en español de códigos de respuesta negativa UDS."""
    NRC = {
        0x10: "Servicio no soportado",
        0x11: "Subfunción no soportada",
        0x12: "Longitud de mensaje incorrecta",
        0x13: "Formato incorrecto",
        0x14: "Límite de respuesta excedido",
        0x21: "Condiciones no correctas",
        0x22: "Condiciones no correctas (2)",
        0x24: "Secuencia de petición incorrecta",
        0x25: "No respondido por subred",
        0x26: "Fallo en ejecución",
        0x31: "Petición fuera de rango",
        0x33: "Acceso de seguridad denegado",
        0x35: "Clave inválida",
        0x36: "Intentos de acceso excedidos",
        0x37: "Tiempo de espera de acceso requerido",
        0x70: "Fallo en upload/download",
        0x71: "Transferencia de datos incorrecta",
        0x72: "Parámetro transferencia fuera de rango",
        0x73: "Bloque de transferencia fuera de secuencia",
        0x78: "Respuesta pendiente",
        0x7E: "Subfunción no soportada en sesión activa",
        0x7F: "Servicio no soportado en sesión activa",
    }
    return NRC.get(codigo, f"Código desconocido (0x{codigo:02X})")
