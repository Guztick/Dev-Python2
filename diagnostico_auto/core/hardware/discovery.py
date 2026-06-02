# -*- coding: utf-8 -*-
"""
Descubrimiento de dispositivos — Bluetooth y USB.

En PC (Windows/Linux/macOS):
  - Enumera todos los puertos seriales disponibles con pyserial.
  - Los adaptadores ELM327 Bluetooth aparecen como puertos COM virtuales
    en Windows (emparéjalos primero desde los ajustes de Bluetooth).
  - Los ELM327 USB aparecen como COM/ttyUSB directamente.

En Android:
  - Bluetooth: API nativa (dispositivos emparejados).
  - USB: UsbManager de Android.
"""
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class DispositivoDescubierto:
    """Un dispositivo encontrado durante el escaneo."""
    nombre: str
    direccion: str           # COM5 / /dev/ttyUSB0 / MAC Bluetooth en Android
    tipo: str                # "bluetooth", "usb" o "serial"
    emparejado: bool = False
    descripcion: str = ""
    probable_obd: bool = False

    def __post_init__(self):
        self.probable_obd = self._es_probable_obd()

    def _es_probable_obd(self) -> bool:
        nombre = self.nombre.upper()
        desc = self.descripcion.upper()
        palabras_clave = [
            "OBD", "ELM", "ELM327", "VLINK", "VGATE", "ICAR",
            "OBDII", "OBD2", "KONNWEI", "VIECAR", "OBDLINK",
            "CARISTA", "SCAN", "DIAG", "STANDARD_SERIAL",
            "SERIAL PORT",  # Nombre genérico de servicio BT SPP en Windows
        ]
        return any(p in nombre or p in desc for p in palabras_clave)


def _es_android() -> bool:
    try:
        import jnius  # noqa: F401
        return True
    except ImportError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Descubridor de puertos seriales (PC)
# ─────────────────────────────────────────────────────────────────────────────

class DescubridorPuertosPC:
    """
    Lista todos los puertos seriales disponibles en el PC.
    Detecta tanto adaptadores USB como puertos COM virtuales BT.
    """

    # Pistas en el nombre/descripción que sugieren un adaptador OBD Bluetooth
    _BT_HINTS = ["bluetooth", "bt port", "serial port", "rfcomm", "spp"]
    # Pistas en el nombre que sugieren USB OBD
    _USB_HINTS = ["usb", "ch340", "cp210", "ftdi", "prolific", "pl2303"]

    def listar(self) -> List[DispositivoDescubierto]:
        dispositivos = []
        try:
            from serial.tools import list_ports
            for p in list_ports.comports():
                desc_raw = (p.description or "").lower()
                nombre = p.description if p.description and p.description != "n/a" else p.device
                fabricante = (p.manufacturer or "").lower()
                info_completa = f"{desc_raw} {fabricante} {(p.hwid or '').lower()}"

                # Determinar si parece BT o USB
                es_bt = any(h in info_completa for h in self._BT_HINTS)
                es_usb = any(h in info_completa for h in self._USB_HINTS)

                tipo = "bluetooth" if es_bt else ("usb" if es_usb else "serial")
                descripcion = f"{p.manufacturer or ''} · {p.hwid or ''}".strip(" ·")

                dispositivos.append(DispositivoDescubierto(
                    nombre=nombre,
                    direccion=p.device,   # COM5, /dev/ttyUSB0, etc.
                    tipo=tipo,
                    emparejado=True,      # Si aparece, el OS ya lo reconoce
                    descripcion=descripcion,
                ))

        except ImportError:
            logger.warning("pyserial no instalado. Instala con: pip install pyserial")
        except Exception as e:
            logger.error(f"Error listando puertos: {e}")

        # Primero los probables OBD, luego los BT, luego el resto
        dispositivos.sort(key=lambda d: (not d.probable_obd, d.tipo != "bluetooth", d.nombre))
        return dispositivos


# ─────────────────────────────────────────────────────────────────────────────
# Descubridores Android (sin cambios)
# ─────────────────────────────────────────────────────────────────────────────

class DescubridorBluetooth:
    """Dispositivos Bluetooth — Android nativo."""

    def listar_emparejados(self) -> List[DispositivoDescubierto]:
        dispositivos = []
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None or not adapter.isEnabled():
                return []
            for dispositivo in adapter.getBondedDevices().toArray():
                dispositivos.append(DispositivoDescubierto(
                    nombre=dispositivo.getName() or "Desconocido",
                    direccion=dispositivo.getAddress(),
                    tipo="bluetooth",
                    emparejado=True,
                    descripcion="Emparejado",
                ))
        except Exception as e:
            logger.error(f"Error BT Android: {e}")
        return dispositivos


class DescubridorUSB:
    """Dispositivos USB — Android nativo."""

    def listar_puertos(self) -> List[DispositivoDescubierto]:
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
                dev = iterador.next()
                nombre = dev.getProductName() or "USB OBD"
                fab = ""
                try:
                    fab = dev.getManufacturerName() or ""
                except Exception:
                    pass
                dispositivos.append(DispositivoDescubierto(
                    nombre=nombre,
                    direccion=dev.getDeviceName(),
                    tipo="usb",
                    descripcion=f"{fab} (VID:{dev.getVendorId()} PID:{dev.getProductId()})",
                ))
        except Exception as e:
            logger.error(f"Error USB Android: {e}")
        return dispositivos


# ─────────────────────────────────────────────────────────────────────────────
# Descubridor unificado
# ─────────────────────────────────────────────────────────────────────────────

class Descubridor:
    """Punto único de descubrimiento — selecciona la estrategia según plataforma."""

    def __init__(self):
        self._android = _es_android()

    def descubrir_todo(self) -> List[DispositivoDescubierto]:
        if self._android:
            return self._descubrir_android()
        return self._descubrir_pc()

    def _descubrir_pc(self) -> List[DispositivoDescubierto]:
        return DescubridorPuertosPC().listar()

    def _descubrir_android(self) -> List[DispositivoDescubierto]:
        dispositivos = []
        dispositivos.extend(DescubridorBluetooth().listar_emparejados())
        dispositivos.extend(DescubridorUSB().listar_puertos())
        dispositivos.sort(key=lambda d: (not d.probable_obd, d.nombre))
        return dispositivos
