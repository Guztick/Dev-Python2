# -*- coding: utf-8 -*-
"""
Descubrimiento de dispositivos — Bluetooth y USB.

Encuentra los adaptadores OBD-II disponibles para conectar:
  - Dispositivos Bluetooth emparejados/cercanos
  - Puertos USB / serial conectados

Funciona en Android (vía pyjnius — APIs nativas) y en escritorio
(vía pyserial y pybluez), detectando la plataforma automáticamente.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DispositivoDescubierto:
    """Un dispositivo encontrado durante el escaneo."""
    nombre: str
    direccion: str           # MAC (Bluetooth) o ruta de puerto (USB)
    tipo: str                # "bluetooth" o "usb"
    emparejado: bool = False
    descripcion: str = ""
    probable_obd: bool = False   # Si el nombre sugiere que es un adaptador OBD

    def __post_init__(self):
        self.probable_obd = self._es_probable_obd()

    def _es_probable_obd(self) -> bool:
        """Detecta si el nombre sugiere un adaptador OBD-II."""
        nombre = self.nombre.upper()
        palabras_clave = [
            "OBD", "ELM", "ELM327", "VLINK", "VGATE", "ICAR",
            "OBDII", "OBD2", "KONNWEI", "VIECAR", "OBDLINK",
            "CARISTA", "SCAN", "DIAG",
        ]
        return any(p in nombre for p in palabras_clave)


def _es_android() -> bool:
    try:
        import jnius  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Bluetooth
# ---------------------------------------------------------------------------

class DescubridorBluetooth:
    """Encuentra dispositivos Bluetooth disponibles."""

    def __init__(self):
        self._android = _es_android()

    def listar_emparejados(self) -> List[DispositivoDescubierto]:
        """
        Lista los dispositivos Bluetooth ya emparejados con el teléfono.
        Es lo más rápido y normalmente el escáner OBD ya está emparejado.
        """
        if self._android:
            return self._emparejados_android()
        return self._emparejados_desktop()

    def _emparejados_android(self) -> List[DispositivoDescubierto]:
        dispositivos = []
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            adapter = BluetoothAdapter.getDefaultAdapter()

            if adapter is None:
                logger.warning("El dispositivo no tiene Bluetooth.")
                return []

            if not adapter.isEnabled():
                logger.warning("El Bluetooth está apagado.")
                return []

            emparejados = adapter.getBondedDevices().toArray()
            for dispositivo in emparejados:
                dispositivos.append(DispositivoDescubierto(
                    nombre=dispositivo.getName() or "Desconocido",
                    direccion=dispositivo.getAddress(),
                    tipo="bluetooth",
                    emparejado=True,
                    descripcion="Dispositivo emparejado",
                ))
        except Exception as e:
            logger.error(f"Error listando Bluetooth en Android: {e}")
        return dispositivos

    def _emparejados_desktop(self) -> List[DispositivoDescubierto]:
        """En escritorio intenta usar pybluez; si no está, retorna vacío."""
        dispositivos = []
        try:
            import bluetooth
            cercanos = bluetooth.discover_devices(duration=8, lookup_names=True)
            for direccion, nombre in cercanos:
                dispositivos.append(DispositivoDescubierto(
                    nombre=nombre or "Desconocido",
                    direccion=direccion,
                    tipo="bluetooth",
                    emparejado=False,
                ))
        except ImportError:
            logger.info("pybluez no instalado — escaneo Bluetooth no disponible en escritorio.")
        except Exception as e:
            logger.error(f"Error escaneando Bluetooth: {e}")
        return dispositivos

    def escanear_cercanos(self, duracion: int = 10) -> List[DispositivoDescubierto]:
        """
        Escanea dispositivos Bluetooth cercanos (no solo emparejados).
        Requiere permiso de ubicación en Android. Tarda más.
        """
        if self._android:
            # El escaneo activo en Android requiere un BroadcastReceiver,
            # más complejo. Por ahora retornamos los emparejados.
            logger.info("Escaneo activo Android: usando dispositivos emparejados.")
            return self._emparejados_android()
        return self._emparejados_desktop()


# ---------------------------------------------------------------------------
# USB / Serial
# ---------------------------------------------------------------------------

class DescubridorUSB:
    """Encuentra adaptadores conectados por USB / serial."""

    def __init__(self):
        self._android = _es_android()

    def listar_puertos(self) -> List[DispositivoDescubierto]:
        """Lista los puertos USB/serial disponibles."""
        if self._android:
            return self._usb_android()
        return self._usb_desktop()

    def _usb_desktop(self) -> List[DispositivoDescubierto]:
        """Enumera puertos serial en escritorio con pyserial."""
        dispositivos = []
        try:
            from serial.tools import list_ports
            for puerto in list_ports.comports():
                descripcion = puerto.description or ""
                nombre = descripcion if descripcion != "n/a" else puerto.device
                disp = DispositivoDescubierto(
                    nombre=nombre,
                    direccion=puerto.device,
                    tipo="usb",
                    descripcion=f"{puerto.manufacturer or ''} {puerto.hwid or ''}".strip(),
                )
                dispositivos.append(disp)
        except ImportError:
            logger.info("pyserial no instalado — enumeración USB no disponible.")
        except Exception as e:
            logger.error(f"Error enumerando puertos USB: {e}")
        return dispositivos

    def _usb_android(self) -> List[DispositivoDescubierto]:
        """Enumera dispositivos USB OTG en Android con UsbManager."""
        dispositivos = []
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            actividad = PythonActivity.mActivity
            usb_manager = cast(
                "android.hardware.usb.UsbManager",
                actividad.getSystemService(Context.USB_SERVICE),
            )
            lista = usb_manager.getDeviceList()
            iterador = lista.values().iterator()
            while iterador.hasNext():
                dispositivo = iterador.next()
                nombre = dispositivo.getProductName() or "Dispositivo USB"
                fabricante = ""
                try:
                    fabricante = dispositivo.getManufacturerName() or ""
                except Exception:
                    pass
                dispositivos.append(DispositivoDescubierto(
                    nombre=nombre,
                    direccion=dispositivo.getDeviceName(),
                    tipo="usb",
                    descripcion=f"{fabricante} (VID:{dispositivo.getVendorId()} "
                                f"PID:{dispositivo.getProductId()})",
                ))
        except Exception as e:
            logger.error(f"Error enumerando USB en Android: {e}")
        return dispositivos


# ---------------------------------------------------------------------------
# Descubridor unificado
# ---------------------------------------------------------------------------

class Descubridor:
    """Punto único para descubrir todos los adaptadores disponibles."""

    def __init__(self):
        self.bluetooth = DescubridorBluetooth()
        self.usb = DescubridorUSB()

    def descubrir_todo(self) -> List[DispositivoDescubierto]:
        """
        Descubre todos los adaptadores disponibles (Bluetooth + USB).
        Ordena poniendo primero los que parecen adaptadores OBD.
        """
        dispositivos = []
        dispositivos.extend(self.bluetooth.listar_emparejados())
        dispositivos.extend(self.usb.listar_puertos())

        # Ordenar: primero los probables OBD, luego por nombre
        dispositivos.sort(key=lambda d: (not d.probable_obd, d.nombre))
        return dispositivos
