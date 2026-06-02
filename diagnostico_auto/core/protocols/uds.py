# -*- coding: utf-8 -*-
"""
Protocolo UDS — Unified Diagnostic Services (ISO 14229-1).

UDS es el protocolo de diagnóstico avanzado que permite acceso a ECUs
de forma granular: leer datos internos, borrar fallos, ejecutar
pruebas de actuadores, e incluso reprogramar módulos.

Es el protocolo que usa el concesionario con sus herramientas propietarias.
A diferencia de OBD-II (que es público), UDS con acceso total requiere
el algoritmo seed/key del fabricante, pero muchos servicios funcionan
sin él en sesión extendida.
"""
import logging
import time
from typing import Optional, List, Tuple, Dict
from ..hardware.elm327 import ELM327

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes de servicios UDS
# ---------------------------------------------------------------------------
class Servicio:
    SESION_DIAGNOSTICA          = 0x10
    RESET_ECU                   = 0x11
    COMUNICACION_SEGURA         = 0x12
    TRANSMITTER_CONTROL         = 0x13
    LIMPIAR_DTCs                = 0x14
    LEER_DTCS                   = 0x19
    LEER_DATO_POR_ID            = 0x22
    LEER_DATO_POR_DIRECCION     = 0x23
    LEER_DATOS_ESCALADOS        = 0x24
    ACCESO_SEGURIDAD            = 0x27
    CONTROL_COMUNICACION        = 0x28
    AUTENTICAR                  = 0x29
    LEER_DATO_PERIODICO         = 0x2A
    DEFINIR_DATO_DINAMICO       = 0x2C
    ESCRIBIR_DATO_POR_ID        = 0x2E
    CONTROL_IO_COMPONENTE       = 0x2F
    CONTROL_RUTINA              = 0x31
    SOLICITAR_DESCARGA          = 0x34
    SOLICITAR_CARGA             = 0x35
    TRANSFERIR_DATOS            = 0x36
    SOLICITAR_FIN_TRANSFERENCIA = 0x37
    TESTER_PRESENTE             = 0x3E
    CONTROL_DTC                 = 0x85
    ENLACE_CONTROL              = 0x87

    # Subfunciones de sesión
    class Sesion:
        DEFAULT     = 0x01
        EXTENDIDA   = 0x03
        PROGRAMACION = 0x02


# DIDs estándar ISO 14229
class DID:
    VIN                   = 0xF190
    ECU_HARDWARE_VERSION  = 0xF191
    ECU_SOFTWARE_VERSION  = 0xF189
    NUMERO_SERIE          = 0xF18C
    NUMERO_PARTE          = 0xF187
    FECHA_FABRICACION     = 0xF18B
    NOMBRE_SISTEMA        = 0xF197
    NOMBRE_ECU            = 0xF198
    VEHICULO_NOMBRE       = 0xF197


class UDS:
    """
    Implementación del protocolo UDS sobre ELM327 con CAN bus.

    Permite diagnóstico avanzado más allá del estándar OBD-II:
    - Identificación completa de ECUs
    - Lectura de DTCs por tipo/estado
    - Datos internos propietarios (por DID)
    - Pruebas de actuadores
    - Sesiones de diagnóstico extendidas
    """

    def __init__(self, adaptador: ELM327, id_solicitud: int, id_respuesta: int):
        """
        Parámetros:
            adaptador:    Instancia ELM327 ya inicializada
            id_solicitud: CAN ID del ECU destino (ej. 0x7E0 motor Renault)
            id_respuesta: CAN ID de respuesta del ECU (ej. 0x7E8)
        """
        self._elm = adaptador
        self._req_id = id_solicitud
        self._resp_id = id_respuesta

    def _enviar(self, servicio: int, datos: bytes = b"", timeout: float = 3.0) -> Optional[bytes]:
        """Envía servicio UDS y retorna bytes de respuesta sin el byte de servicio."""
        respuesta = self._elm.enviar_uds(
            id_destino=self._req_id,
            id_respuesta=self._resp_id,
            servicio=servicio,
            datos=datos,
            timeout=timeout,
        )
        if respuesta and len(respuesta) > 0:
            # Saltar byte de servicio de respuesta (servicio + 0x40)
            return respuesta[1:] if len(respuesta) > 1 else b""
        return None

    # ------------------------------------------------------------------
    # Sesiones de diagnóstico
    # ------------------------------------------------------------------

    def abrir_sesion_extendida(self) -> bool:
        """
        Cambia a sesión diagnóstica extendida (0x03).
        Habilita más servicios sin necesitar acceso de seguridad.
        """
        resp = self._enviar(Servicio.SESION_DIAGNOSTICA,
                            bytes([Servicio.Sesion.EXTENDIDA]))
        return resp is not None

    def abrir_sesion_default(self) -> bool:
        """Vuelve a la sesión por defecto (termina sesión extendida/programación)."""
        resp = self._enviar(Servicio.SESION_DIAGNOSTICA,
                            bytes([Servicio.Sesion.DEFAULT]))
        return resp is not None

    def mantener_sesion_activa(self) -> bool:
        """
        Envía TesterPresent (0x3E) para que el ECU no cierre la sesión.
        Llamar periódicamente si la sesión extendida lleva más de 5 segundos.
        """
        resp = self._enviar(Servicio.TESTER_PRESENTE, bytes([0x00]))
        return resp is not None

    def reset_ecu(self, tipo: int = 0x01) -> bool:
        """
        Reinicia el ECU.
        tipo: 0x01 = hard reset, 0x02 = key off/on, 0x03 = soft reset
        """
        resp = self._enviar(Servicio.RESET_ECU, bytes([tipo]), timeout=5.0)
        return resp is not None

    # ------------------------------------------------------------------
    # Lectura de datos por ID (Servicio 0x22)
    # ------------------------------------------------------------------

    def leer_dato(self, did: int) -> Optional[bytes]:
        """Lee un Data Identifier (DID) del ECU. Retorna bytes crudos."""
        datos_req = bytes([did >> 8, did & 0xFF])
        return self._enviar(Servicio.LEER_DATO_POR_ID, datos_req)

    def leer_vin(self) -> Optional[str]:
        datos = self.leer_dato(DID.VIN)
        if datos:
            return datos.decode("ascii", errors="ignore").strip("\x00").strip()
        return None

    def leer_version_software(self) -> Optional[str]:
        datos = self.leer_dato(DID.ECU_SOFTWARE_VERSION)
        if datos:
            return datos.decode("ascii", errors="ignore").strip("\x00").strip()
        return None

    def leer_version_hardware(self) -> Optional[str]:
        datos = self.leer_dato(DID.ECU_HARDWARE_VERSION)
        if datos:
            return datos.decode("ascii", errors="ignore").strip("\x00").strip()
        return None

    def leer_numero_parte(self) -> Optional[str]:
        datos = self.leer_dato(DID.NUMERO_PARTE)
        if datos:
            return datos.decode("ascii", errors="ignore").strip("\x00").strip()
        return None

    def leer_numero_serie(self) -> Optional[str]:
        datos = self.leer_dato(DID.NUMERO_SERIE)
        if datos:
            return datos.hex().upper()
        return None

    def leer_info_completa(self) -> Dict[str, Optional[str]]:
        """Lee toda la información de identificación del ECU."""
        return {
            "VIN": self.leer_vin(),
            "Número de parte": self.leer_numero_parte(),
            "Número de serie": self.leer_numero_serie(),
            "Versión software": self.leer_version_software(),
            "Versión hardware": self.leer_version_hardware(),
        }

    # ------------------------------------------------------------------
    # Lectura de DTCs (Servicio 0x19)
    # ------------------------------------------------------------------

    def leer_dtcs(self, sub_funcion: int = 0x02) -> List[Tuple[str, int]]:
        """
        Lee DTCs usando el servicio UDS ReadDTCInformation.
        Retorna lista de (código_dtc, byte_estado).

        Sub-funciones:
          0x01 — número de DTCs por máscara de estado
          0x02 — DTCs por máscara de estado (todos los activos/históricos)
          0x06 — DTCs por tipo (más detallado)
          0x0A — todos los DTCs con datos de snapshot
        """
        # Máscara 0xFF = cualquier estado (activo, historial, pendiente, etc.)
        resp = self._enviar(
            Servicio.LEER_DTCS,
            bytes([sub_funcion, 0xFF]),
            timeout=5.0,
        )
        if not resp or len(resp) < 3:
            return []

        dtcs = []
        # Respuesta: [sub_fn, byte_registro_dtc, DTC1_high, DTC1_med, DTC1_low, estado1, ...]
        idx = 1  # saltar byte de sub-función en respuesta
        if idx < len(resp):
            idx += 1  # saltar byte de registro del tamaño de registro DTC (0x04 = 4 bytes)

        while idx + 3 < len(resp):
            dtc_bytes = resp[idx:idx + 3]
            estado = resp[idx + 3]
            dtc_str = self._bytes_a_dtc(dtc_bytes)
            if dtc_str:
                dtcs.append((dtc_str, estado))
            idx += 4

        return dtcs

    def limpiar_dtcs(self) -> bool:
        """Borra toda la información de diagnóstico almacenada en el ECU."""
        # 0xFFFFFF = grupo universal (todos los DTCs)
        resp = self._enviar(Servicio.LIMPIAR_DTCs, bytes([0xFF, 0xFF, 0xFF]), timeout=5.0)
        return resp is not None

    @staticmethod
    def _bytes_a_dtc(data: bytes) -> Optional[str]:
        """Convierte 3 bytes ISO-14229 a string DTC (ej. P0300)."""
        if len(data) < 3:
            return None
        tipo = (data[0] >> 6) & 0x03
        prefijo = ["P", "C", "B", "U"][tipo]
        numero = ((data[0] & 0x3F) << 8) | data[1]
        return f"{prefijo}{numero:04X}"

    # ------------------------------------------------------------------
    # Acceso de seguridad (Servicio 0x27) — Seed/Key
    # ------------------------------------------------------------------

    def solicitar_seed(self, nivel: int = 0x01) -> Optional[bytes]:
        """
        Solicita el seed para desbloqueo de seguridad.
        El ECU devuelve un número aleatorio (seed).
        Para obtener acceso, debes calcular la key con el algoritmo del fabricante.
        """
        resp = self._enviar(Servicio.ACCESO_SEGURIDAD, bytes([nivel]))
        return resp  # Los bytes son el seed — la key debe calcularse

    def enviar_key(self, nivel_respuesta: int, key: bytes) -> bool:
        """
        Envía la key calculada para desbloquear el ECU.
        nivel_respuesta es generalmente nivel_seed + 1.
        """
        resp = self._enviar(
            Servicio.ACCESO_SEGURIDAD,
            bytes([nivel_respuesta]) + key,
        )
        return resp is not None

    # ------------------------------------------------------------------
    # Control de rutinas (Servicio 0x31)
    # ------------------------------------------------------------------

    def ejecutar_rutina(self, id_rutina: int, datos: bytes = b"") -> Optional[bytes]:
        """
        Ejecuta una rutina interna del ECU.
        Las rutinas disponibles varían por marca/modelo.
        Ej: reset de adaptaciones, prueba de inyectores, inicialización DPF.
        """
        req = bytes([0x01, id_rutina >> 8, id_rutina & 0xFF]) + datos
        return self._enviar(Servicio.CONTROL_RUTINA, req, timeout=10.0)

    def verificar_rutina(self, id_rutina: int) -> Optional[bytes]:
        """Verifica el resultado de la última rutina ejecutada."""
        req = bytes([0x03, id_rutina >> 8, id_rutina & 0xFF])
        return self._enviar(Servicio.CONTROL_RUTINA, req)

    # ------------------------------------------------------------------
    # Control de I/O — actuadores (Servicio 0x2F)
    # ------------------------------------------------------------------

    def controlar_actuador(self, id_dato: int, modo_control: int,
                           valor: bytes = b"") -> Optional[bytes]:
        """
        Controla una salida del ECU (válvulas, relevadores, motores).
        modo_control: 0x00=retornar control, 0x01=reset, 0x03=ajustar corto
        """
        req = bytes([id_dato >> 8, id_dato & 0xFF, modo_control]) + valor
        return self._enviar(Servicio.CONTROL_IO_COMPONENTE, req, timeout=5.0)

    # ------------------------------------------------------------------
    # Detección de capacidades del ECU
    # ------------------------------------------------------------------

    def detectar_servicios_soportados(self) -> List[int]:
        """
        Detecta qué servicios UDS responde este ECU.
        Prueba los servicios principales y registra cuáles están disponibles.
        """
        servicios_a_probar = [
            Servicio.SESION_DIAGNOSTICA,
            Servicio.RESET_ECU,
            Servicio.LIMPIAR_DTCs,
            Servicio.LEER_DTCS,
            Servicio.LEER_DATO_POR_ID,
            Servicio.ACCESO_SEGURIDAD,
            Servicio.CONTROL_COMUNICACION,
            Servicio.CONTROL_RUTINA,
            Servicio.CONTROL_IO_COMPONENTE,
            Servicio.TESTER_PRESENTE,
            Servicio.CONTROL_DTC,
        ]

        soportados = []
        for servicio in servicios_a_probar:
            # Enviar solicitud mínima — si hay respuesta (positiva o NRC que no sea 0x11)
            # el servicio existe pero puede requerir parámetros
            resp_raw = self._elm._conn.enviar_recibir(
                self._construir_frame_uds(servicio, b"\x00"),
                timeout=1.5,
            )
            if resp_raw and "TIMEOUT" not in resp_raw and "NO DATA" not in resp_raw:
                # NRC 0x11 = servicio no soportado, cualquier otra respuesta = existe
                partes = resp_raw.split()
                try:
                    nrc = [int(p, 16) for p in partes]
                    # Si no hay 0x7F con 0x11, el servicio responde
                    if not (len(nrc) >= 3 and nrc[0] == 0x7F and nrc[2] == 0x11):
                        soportados.append(servicio)
                except ValueError:
                    pass
            time.sleep(0.1)

        return soportados

    def _construir_frame_uds(self, servicio: int, datos: bytes) -> str:
        payload = bytes([servicio]) + datos
        return " ".join(f"{b:02X}" for b in payload)
