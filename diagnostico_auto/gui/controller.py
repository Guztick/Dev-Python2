# -*- coding: utf-8 -*-
"""
Controlador de la aplicación — capa intermedia entre la UI y el motor.

Gestiona el estado de conexión, ejecuta operaciones de diagnóstico en
hilos secundarios (para no congelar la UI) y provee datos de demostración
realistas del Renault Duster cuando no hay hardware conectado.

Esto permite desarrollar y probar toda la interfaz sin un adaptador físico.
"""
import threading
import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class EstadoConexion(Enum):
    DESCONECTADO = "desconectado"
    CONECTANDO   = "conectando"
    CONECTADO    = "conectado"
    ERROR        = "error"


class TipoAdaptador(Enum):
    WIFI      = "WiFi"
    BLUETOOTH = "Bluetooth"
    USB       = "USB"
    DEMO      = "Demo"


@dataclass
class InfoVehiculo:
    """Información del vehículo conectado."""
    marca: str = "Renault"
    modelo: str = "Duster"
    vin: Optional[str] = None
    año: Optional[str] = None
    motor: Optional[str] = None
    protocolo: Optional[str] = None
    voltaje: Optional[float] = None


class Controlador:
    """
    Controlador central de la aplicación.

    Mantiene el estado de conexión y orquesta las operaciones de
    diagnóstico, ejecutándolas en hilos para mantener la UI fluida.
    """

    def __init__(self):
        self.estado = EstadoConexion.DESCONECTADO
        self.tipo_adaptador: Optional[TipoAdaptador] = None
        self.info_vehiculo = InfoVehiculo()
        self.modo_demo = True

        self._elm = None
        self._modulos = None
        self._callbacks_estado: List[Callable] = []

        # Cargar perfil del Duster
        try:
            from brands.renault.duster import PerfilDuster
            self._perfil = PerfilDuster
            self._modulos = PerfilDuster.modulos()
        except Exception as e:
            logger.error(f"Error cargando perfil: {e}")
            self._perfil = None

    # ------------------------------------------------------------------
    # Observadores de estado (para que la UI reaccione a cambios)
    # ------------------------------------------------------------------

    def suscribir_estado(self, callback: Callable[[EstadoConexion], None]) -> None:
        """Registra un callback que se llama cuando cambia el estado."""
        self._callbacks_estado.append(callback)

    def _notificar_estado(self) -> None:
        for cb in self._callbacks_estado:
            try:
                cb(self.estado)
            except Exception as e:
                logger.debug(f"Error en callback de estado: {e}")

    def _set_estado(self, estado: EstadoConexion) -> None:
        self.estado = estado
        self._notificar_estado()

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def conectar(
        self,
        tipo: TipoAdaptador,
        direccion: str = "",
        on_completo: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """
        Conecta a un adaptador en un hilo secundario.

        Parámetros:
            tipo:        WiFi, Bluetooth, USB o Demo
            direccion:   IP, MAC o puerto según el tipo
            on_completo: callback(exito, mensaje) al terminar
        """
        self.tipo_adaptador = tipo
        self.modo_demo = (tipo == TipoAdaptador.DEMO)
        self._set_estado(EstadoConexion.CONECTANDO)

        hilo = threading.Thread(
            target=self._conectar_worker,
            args=(tipo, direccion, on_completo),
            daemon=True,
        )
        hilo.start()

    def _conectar_worker(self, tipo, direccion, on_completo) -> None:
        try:
            if tipo == TipoAdaptador.DEMO:
                time.sleep(1.5)  # Simular tiempo de conexión
                self._cargar_datos_demo()
                self._set_estado(EstadoConexion.CONECTADO)
                if on_completo:
                    on_completo(True, "Conectado en modo demostración")
                return

            # Conexión real con hardware
            from core.hardware.base import ConexionWiFi, ConexionSerial, ConexionBluetooth
            from core.hardware.elm327 import ELM327

            if tipo == TipoAdaptador.WIFI:
                ip, _, puerto = direccion.partition(":")
                conexion = ConexionWiFi(host=ip or "192.168.0.10",
                                        puerto=int(puerto) if puerto else 35000)
            elif tipo == TipoAdaptador.BLUETOOTH:
                conexion = ConexionBluetooth(direccion_mac=direccion)
            elif tipo == TipoAdaptador.USB:
                conexion = ConexionSerial(puerto=direccion)
            else:
                raise ValueError(f"Tipo de adaptador no soportado: {tipo}")

            self._elm = ELM327(conexion)
            if not self._elm.conectar():
                self._set_estado(EstadoConexion.ERROR)
                if on_completo:
                    on_completo(False, "No se pudo conectar al adaptador")
                return

            # Leer información inicial del vehículo
            self.info_vehiculo.protocolo = self._elm.protocolo_activo
            self.info_vehiculo.voltaje = self._elm.leer_voltage_bateria()

            from core.protocols.obd2 import OBD2
            obd = OBD2(self._elm)
            self.info_vehiculo.vin = obd.leer_vin()

            self._set_estado(EstadoConexion.CONECTADO)
            if on_completo:
                on_completo(True, "Conectado correctamente")

        except Exception as e:
            logger.error(f"Error de conexión: {e}")
            self._set_estado(EstadoConexion.ERROR)
            if on_completo:
                on_completo(False, str(e))

    def desconectar(self) -> None:
        """Cierra la conexión actual."""
        if self._elm:
            try:
                self._elm.desconectar()
            except Exception:
                pass
            self._elm = None
        self._set_estado(EstadoConexion.DESCONECTADO)
        self.info_vehiculo = InfoVehiculo()

    @property
    def conectado(self) -> bool:
        return self.estado == EstadoConexion.CONECTADO

    # ------------------------------------------------------------------
    # Descubrimiento de dispositivos (Bluetooth / USB)
    # ------------------------------------------------------------------

    def descubrir_dispositivos(self, on_completo: Callable[[list], None]) -> None:
        """Busca adaptadores Bluetooth y USB disponibles en un hilo."""
        hilo = threading.Thread(
            target=self._descubrir_worker, args=(on_completo,), daemon=True)
        hilo.start()

    def _descubrir_worker(self, on_completo) -> None:
        if self.modo_demo:
            time.sleep(1.5)
            on_completo(self._dispositivos_demo())
            return
        try:
            from core.hardware.discovery import Descubridor
            descubridor = Descubridor()
            dispositivos = descubridor.descubrir_todo()
            on_completo(dispositivos)
        except Exception as e:
            logger.error(f"Error descubriendo dispositivos: {e}")
            on_completo([])

    def _dispositivos_demo(self) -> list:
        """Dispositivos de demostración para previsualizar la UI."""
        from core.hardware.discovery import DispositivoDescubierto
        return [
            DispositivoDescubierto(
                nombre="OBDII", direccion="00:1D:A5:68:98:8B",
                tipo="bluetooth", emparejado=True,
                descripcion="Adaptador emparejado"),
            DispositivoDescubierto(
                nombre="Vgate iCar Pro", direccion="00:10:CC:4F:36:03",
                tipo="bluetooth", emparejado=True,
                descripcion="Adaptador emparejado"),
            DispositivoDescubierto(
                nombre="Audífonos JBL", direccion="A4:77:58:1C:2D:9E",
                tipo="bluetooth", emparejado=True,
                descripcion="Dispositivo emparejado"),
        ]

    # ------------------------------------------------------------------
    # Detección de información del adaptador (escáner)
    # ------------------------------------------------------------------

    def detectar_adaptador(self, on_completo: Callable[[object], None]) -> None:
        """Interroga al adaptador para obtener sus detalles técnicos."""
        hilo = threading.Thread(
            target=self._detectar_adaptador_worker, args=(on_completo,), daemon=True)
        hilo.start()

    def _detectar_adaptador_worker(self, on_completo) -> None:
        if self.modo_demo:
            time.sleep(1.2)
            on_completo(self._info_adaptador_demo())
            return
        try:
            from core.hardware.adapter_info import DetectorAdaptador
            tipo = self.tipo_adaptador.value if self.tipo_adaptador else ""
            detector = DetectorAdaptador(self._elm._conn, tipo_conexion=tipo)
            info = detector.detectar()
            on_completo(info)
        except Exception as e:
            logger.error(f"Error detectando adaptador: {e}")
            on_completo(None)

    def _info_adaptador_demo(self):
        """Info de adaptador de demostración (clon ELM327 v1.5 típico)."""
        from core.hardware.adapter_info import InfoAdaptador
        from core.protocols import obd2  # noqa
        from core.hardware.elm327 import PROTOCOLOS
        info = InfoAdaptador(
            identidad="ELM327 v1.5",
            descripcion="OBDII to RS232 Interpreter",
            identificador="?",
            version_elm="1.5",
            fabricante_chip="ELM327 compatible (clon habitual)",
            es_genuino=False,
            voltaje=14.2,
            protocolo_actual="ISO 15765-4 CAN (11 bit ID, 500 kbps)",
            tipo_conexion=self.tipo_adaptador.value if self.tipo_adaptador else "Bluetooth",
        )
        info.protocolos_soportados = [
            n for c, n in PROTOCOLOS.items() if c != "0"]
        return info

    # ------------------------------------------------------------------
    # Datos de demostración (Renault Duster realista)
    # ------------------------------------------------------------------

    def _cargar_datos_demo(self) -> None:
        self.info_vehiculo = InfoVehiculo(
            marca="Renault",
            modelo="Duster",
            vin="93YHSRDH4LJ123456",
            año="2020",
            motor="1.6 SCe H4M (110 CV)",
            protocolo="ISO 15765-4 CAN 500kbps 11-bit",
            voltaje=14.2,
        )

    # ------------------------------------------------------------------
    # Escaneo de capacidades
    # ------------------------------------------------------------------

    def escanear_capacidades(
        self,
        on_progreso: Callable[[str, float], None],
        on_completo: Callable[[object], None],
    ) -> None:
        """Ejecuta el escaneo de capacidades en un hilo."""
        hilo = threading.Thread(
            target=self._escanear_worker,
            args=(on_progreso, on_completo),
            daemon=True,
        )
        hilo.start()

    def _escanear_worker(self, on_progreso, on_completo) -> None:
        if self.modo_demo:
            resultado = self._escaneo_demo(on_progreso)
            on_completo(resultado)
            return

        try:
            from diagnostics.capability_scanner import EscanerCapacidades
            escaner = EscanerCapacidades(self._elm, callback_progreso=on_progreso)
            reporte = escaner.escanear_vehiculo(self._perfil.modulos_principales())
            on_completo(reporte)
        except Exception as e:
            logger.error(f"Error en escaneo: {e}")
            on_completo(None)

    def _escaneo_demo(self, on_progreso) -> List[Dict]:
        """Simula un escaneo de capacidades con resultados realistas."""
        modulos_demo = [
            {"nombre": "UCE/PCM", "desc": "Unidad de Control del Motor",
             "presente": True, "nivel": 3, "dtcs": 2, "rutinas": True, "actuadores": True},
            {"nombre": "TCM/EDC", "desc": "Control de Transmisión",
             "presente": True, "nivel": 2, "dtcs": 0, "rutinas": True, "actuadores": False},
            {"nombre": "ABS/ESP", "desc": "Frenos antibloqueo y estabilidad",
             "presente": True, "nivel": 3, "dtcs": 1, "rutinas": True, "actuadores": True},
            {"nombre": "AIRBAG", "desc": "Sistema de bolsas de aire",
             "presente": True, "nivel": 2, "dtcs": 0, "rutinas": False, "actuadores": False},
            {"nombre": "UCH", "desc": "Unidad Central de Habitáculo",
             "presente": True, "nivel": 2, "dtcs": 0, "rutinas": True, "actuadores": True},
            {"nombre": "EPS", "desc": "Dirección asistida eléctrica",
             "presente": True, "nivel": 2, "dtcs": 0, "rutinas": False, "actuadores": False},
            {"nombre": "CLUSTER", "desc": "Cuadro de instrumentos",
             "presente": True, "nivel": 1, "dtcs": 0, "rutinas": False, "actuadores": False},
            {"nombre": "HVAC", "desc": "Control de climatización",
             "presente": False, "nivel": 0, "dtcs": 0, "rutinas": False, "actuadores": False},
        ]

        total = len(modulos_demo)
        for i, mod in enumerate(modulos_demo):
            pct = 10 + (i / total) * 85
            on_progreso(f"Probando {mod['nombre']}...", pct)
            time.sleep(0.4)

        on_progreso("Escaneo completo", 100)
        return modulos_demo

    # ------------------------------------------------------------------
    # Lectura de DTCs
    # ------------------------------------------------------------------

    def leer_dtcs(self, on_completo: Callable[[Dict], None]) -> None:
        hilo = threading.Thread(
            target=self._leer_dtcs_worker, args=(on_completo,), daemon=True)
        hilo.start()

    def _leer_dtcs_worker(self, on_completo) -> None:
        if self.modo_demo:
            time.sleep(1.2)
            on_completo(self._dtcs_demo())
            return

        try:
            from diagnostics.dtc_reader import LectorDTCs
            lector = LectorDTCs(self._elm)
            resultado = lector.leer_todos(self._modulos)
            on_completo(resultado)
        except Exception as e:
            logger.error(f"Error leyendo DTCs: {e}")
            on_completo({})

    def _dtcs_demo(self) -> Dict[str, List[Dict]]:
        """DTCs de demostración con casos realistas del Duster."""
        return {
            "Motor (UCE)": [
                {"codigo": "P0401", "desc": "Flujo insuficiente del sistema de recirculación EGR",
                 "activo": True, "severidad": "media"},
                {"codigo": "P0341", "desc": "Sensor de posición del árbol de levas — rango/rendimiento",
                 "activo": False, "severidad": "baja"},
            ],
            "Frenos (ABS/ESP)": [
                {"codigo": "C0035", "desc": "Sensor de velocidad de rueda delantera izquierda — circuito",
                 "activo": True, "severidad": "alta"},
            ],
        }

    # ------------------------------------------------------------------
    # Datos en tiempo real
    # ------------------------------------------------------------------

    def leer_datos_vivo(self) -> Dict[str, tuple]:
        """
        Retorna un snapshot de datos en tiempo real.
        Formato: {nombre: (valor, unidad)}
        """
        if self.modo_demo:
            return self._datos_vivo_demo()

        try:
            from core.protocols.obd2 import OBD2
            obd = OBD2(self._elm)
            return obd.leer_todos_los_pids()
        except Exception as e:
            logger.debug(f"Error datos vivo: {e}")
            return {}

    def _datos_vivo_demo(self) -> Dict[str, tuple]:
        """Genera datos en vivo simulados con variación realista."""
        base = time.time()
        rpm = 820 + random.randint(-40, 60) + int(abs(150 * (random.random() - 0.5)))
        return {
            "RPM motor":               (rpm, "rpm"),
            "Velocidad":               (0, "km/h"),
            "Temp. refrigerante":      (89 + random.randint(-2, 3), "°C"),
            "Temp. aceite":            (95 + random.randint(-3, 4), "°C"),
            "Carga del motor":         (round(18 + random.uniform(-3, 5), 1), "%"),
            "Posición acelerador":     (round(14 + random.uniform(-2, 2), 1), "%"),
            "Presión colector":        (32 + random.randint(-2, 2), "kPa"),
            "Flujo de aire (MAF)":     (round(3.2 + random.uniform(-0.4, 0.6), 2), "g/s"),
            "Avance de encendido":     (round(12 + random.uniform(-2, 3), 1), "°"),
            "Voltaje batería":         (round(14.1 + random.uniform(-0.2, 0.2), 1), "V"),
            "Temp. admisión":          (38 + random.randint(-2, 3), "°C"),
            "Nivel combustible":       (round(62 + random.uniform(-0.5, 0.5), 1), "%"),
        }


# Instancia única global del controlador
controlador = Controlador()
