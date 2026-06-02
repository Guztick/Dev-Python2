# -*- coding: utf-8 -*-
"""
Gestor de drivers para adaptadores OBD-II en PC.

Los adaptadores ELM327 USB usan chips conversores USB-serial. Cada chip
necesita su driver para que el sistema cree el puerto COM. Este módulo:

  - Identifica el chip de un adaptador por su VID/PID.
  - Detecta si el driver está instalado (Windows: vía PowerShell).
  - Encuentra dispositivos USB sin driver (signo de admiración en el
    Administrador de dispositivos).
  - Ofrece instalar el driver correcto (instalador local o descarga oficial).

Los adaptadores Bluetooth usan el stack Bluetooth del sistema (perfil SPP),
que no requiere driver adicional — solo emparejar y usar el puerto COM
saliente que Windows crea automáticamente.
"""
import os
import sys
import logging
import subprocess
import webbrowser
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class EstadoDriver(Enum):
    INSTALADO   = "instalado"     # El puerto COM existe y funciona
    FALTANTE    = "faltante"      # Dispositivo presente pero sin driver
    DESCONOCIDO = "desconocido"   # No se pudo determinar


@dataclass
class ChipUSB:
    """Información de un chip conversor USB-serial usado en adaptadores OBD."""
    nombre: str
    vid: str                       # Vendor ID en hex sin prefijo, ej "1A86"
    pids: List[str]                # Product IDs posibles
    driver_nombre: str
    driver_url: str
    instalador_local: str = ""     # Nombre del .exe en la carpeta drivers/ (si existe)
    descripcion: str = ""

    def coincide(self, vid: str, pid: str) -> bool:
        return (vid or "").upper() == self.vid.upper() and \
               (pid or "").upper() in [p.upper() for p in self.pids]


# Base de datos de chips comunes en adaptadores ELM327
CHIPS_CONOCIDOS: List[ChipUSB] = [
    ChipUSB(
        nombre="CH340 / CH341",
        vid="1A86", pids=["7523", "5523", "5512"],
        driver_nombre="WCH CH341SER",
        driver_url="https://www.wch-ic.com/downloads/CH341SER_EXE.html",
        instalador_local="CH341SER.EXE",
        descripcion="El chip más común en clones ELM327 USB económicos.",
    ),
    ChipUSB(
        nombre="CP210x (Silicon Labs)",
        vid="10C4", pids=["EA60", "EA61", "EA70"],
        driver_nombre="Silicon Labs CP210x VCP",
        driver_url="https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers",
        instalador_local="CP210xVCPInstaller_x64.exe",
        descripcion="Chip de calidad usado en adaptadores de gama media.",
    ),
    ChipUSB(
        nombre="FTDI FT232",
        vid="0403", pids=["6001", "6010", "6011", "6014", "6015"],
        driver_nombre="FTDI VCP",
        driver_url="https://ftdichip.com/drivers/vcp-drivers/",
        instalador_local="CDM212364_Setup.exe",
        descripcion="Chip premium, presente en OBDLink y adaptadores genuinos.",
    ),
    ChipUSB(
        nombre="PL2303 (Prolific)",
        vid="067B", pids=["2303", "2304", "23A3", "23B3", "23C3", "23D3"],
        driver_nombre="Prolific PL2303",
        driver_url="https://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41",
        instalador_local="PL2303_Prolific_Driver.exe",
        descripcion="Chip antiguo; muchos clones no funcionan con drivers nuevos.",
    ),
    ChipUSB(
        nombre="STN11xx / STN21xx (OBDLink)",
        vid="0403", pids=["6015"],
        driver_nombre="FTDI VCP (OBDLink)",
        driver_url="https://ftdichip.com/drivers/vcp-drivers/",
        instalador_local="CDM212364_Setup.exe",
        descripcion="Chip de los adaptadores OBDLink genuinos (premium).",
    ),
]


@dataclass
class DispositivoDriver:
    """Un dispositivo detectado con su estado de driver."""
    nombre: str
    vid: str = ""
    pid: str = ""
    puerto: str = ""               # COM3 si tiene driver, vacío si falta
    estado: EstadoDriver = EstadoDriver.DESCONOCIDO
    chip: Optional[ChipUSB] = None
    instance_id: str = ""

    @property
    def necesita_driver(self) -> bool:
        return self.estado == EstadoDriver.FALTANTE

    @property
    def nombre_chip(self) -> str:
        return self.chip.nombre if self.chip else "Chip desconocido"


def _es_windows() -> bool:
    return os.name == "nt"


def _carpeta_drivers() -> str:
    """Ruta a la carpeta drivers/ en la raíz del proyecto."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(base, "drivers")


def identificar_chip(vid: str, pid: str) -> Optional[ChipUSB]:
    """Busca el chip que coincide con un VID/PID dado."""
    for chip in CHIPS_CONOCIDOS:
        if chip.coincide(vid, pid):
            return chip
    return None


def _parse_vid_pid(texto: str) -> tuple:
    """Extrae VID y PID de una cadena como 'USB VID:PID=1A86:7523' o 'USB\\VID_1A86&PID_7523'."""
    import re
    vid = pid = ""
    # Formato pyserial: "USB VID:PID=1A86:7523"
    m = re.search(r"VID[:_]([0-9A-Fa-f]{4}).{0,3}PID[:_]([0-9A-Fa-f]{4})", texto)
    if m:
        vid, pid = m.group(1).upper(), m.group(2).upper()
    return vid, pid


class GestorDrivers:
    """Detecta y gestiona los drivers de los adaptadores OBD en PC."""

    # ----------------------------------------------------------------
    # Detección de dispositivos con driver (puertos COM existentes)
    # ----------------------------------------------------------------

    def detectar_con_driver(self) -> List[DispositivoDriver]:
        """Lista los dispositivos serie que YA tienen driver (puertos COM)."""
        dispositivos = []
        try:
            from serial.tools import list_ports
            for p in list_ports.comports():
                vid = f"{p.vid:04X}" if p.vid else ""
                pid = f"{p.pid:04X}" if p.pid else ""
                if not vid:
                    vid, pid = _parse_vid_pid(p.hwid or "")
                chip = identificar_chip(vid, pid)
                dispositivos.append(DispositivoDriver(
                    nombre=p.description or p.device,
                    vid=vid, pid=pid,
                    puerto=p.device,
                    estado=EstadoDriver.INSTALADO,
                    chip=chip,
                    instance_id=p.hwid or "",
                ))
        except ImportError:
            logger.warning("pyserial no instalado.")
        except Exception as e:
            logger.error(f"Error detectando puertos: {e}")
        return dispositivos

    # ----------------------------------------------------------------
    # Detección de dispositivos SIN driver (solo Windows, vía PowerShell)
    # ----------------------------------------------------------------

    def detectar_sin_driver(self) -> List[DispositivoDriver]:
        """
        Encuentra dispositivos USB presentes pero con problemas de driver
        (Status = Error en el Administrador de dispositivos).
        Solo funciona en Windows.
        """
        if not _es_windows():
            return []

        dispositivos = []
        try:
            comando = (
                "Get-PnpDevice -PresentOnly | "
                "Where-Object { $_.Status -eq 'Error' -or $_.ConfigManagerErrorCode -ne 0 } | "
                "Select-Object Name, InstanceId, Status | ConvertTo-Json -Compress"
            )
            salida = self._powershell(comando)
            if not salida:
                return []

            import json
            datos = json.loads(salida)
            if isinstance(datos, dict):
                datos = [datos]

            for d in datos:
                instance = d.get("InstanceId", "")
                vid, pid = _parse_vid_pid(instance)
                chip = identificar_chip(vid, pid)
                # Solo reportar si es un chip OBD conocido o un dispositivo USB serie
                if chip or "USB" in instance.upper():
                    dispositivos.append(DispositivoDriver(
                        nombre=d.get("Name", "Dispositivo USB desconocido"),
                        vid=vid, pid=pid,
                        puerto="",
                        estado=EstadoDriver.FALTANTE,
                        chip=chip,
                        instance_id=instance,
                    ))
        except Exception as e:
            logger.error(f"Error detectando dispositivos sin driver: {e}")
        return dispositivos

    def _powershell(self, comando: str, timeout: int = 15) -> str:
        """Ejecuta un comando PowerShell y retorna su salida (Windows)."""
        if not _es_windows():
            return ""
        try:
            startupinfo = None
            creationflags = 0
            if hasattr(subprocess, "STARTUPINFO"):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            resultado = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                capture_output=True, text=True, timeout=timeout,
                startupinfo=startupinfo, creationflags=creationflags,
            )
            return resultado.stdout.strip()
        except Exception as e:
            logger.error(f"Error ejecutando PowerShell: {e}")
            return ""

    # ----------------------------------------------------------------
    # Diagnóstico completo
    # ----------------------------------------------------------------

    def diagnosticar(self) -> List[DispositivoDriver]:
        """
        Diagnóstico completo: dispositivos con driver + dispositivos que
        necesitan driver. Lo que la UI muestra al usuario.
        """
        con_driver = self.detectar_con_driver()
        sin_driver = self.detectar_sin_driver()
        # Evitar duplicados por instance_id
        vistos = {d.instance_id for d in con_driver}
        combinados = list(con_driver)
        for d in sin_driver:
            if d.instance_id not in vistos:
                combinados.append(d)
        return combinados

    # ----------------------------------------------------------------
    # Instalación de drivers
    # ----------------------------------------------------------------

    def instalador_disponible(self, chip: ChipUSB) -> Optional[str]:
        """Retorna la ruta del instalador local si existe en drivers/."""
        if not chip.instalador_local:
            return None
        ruta = os.path.join(_carpeta_drivers(), chip.instalador_local)
        return ruta if os.path.exists(ruta) else None

    def instalar_driver(self, chip: ChipUSB) -> tuple:
        """
        Intenta instalar el driver del chip.

        Si hay un instalador local en drivers/, lo ejecuta (Windows pedirá
        permisos de administrador). Si no, abre la página de descarga oficial.

        Retorna (exito: bool, mensaje: str).
        """
        ruta_local = self.instalador_disponible(chip)

        if ruta_local and _es_windows():
            try:
                # os.startfile lanza el instalador con su propio UAC
                os.startfile(ruta_local)  # type: ignore[attr-defined]
                return True, f"Ejecutando instalador: {chip.instalador_local}"
            except Exception as e:
                logger.error(f"Error ejecutando instalador: {e}")
                # Caer a descarga web
        elif ruta_local:
            # Linux/macOS — abrir la carpeta
            try:
                if sys.platform == "darwin":
                    subprocess.Popen(["open", ruta_local])
                else:
                    subprocess.Popen(["xdg-open", ruta_local])
                return True, f"Abriendo: {chip.instalador_local}"
            except Exception:
                pass

        # No hay instalador local — abrir la descarga oficial
        try:
            webbrowser.open(chip.driver_url)
            return True, f"Abriendo descarga oficial de {chip.driver_nombre}"
        except Exception as e:
            return False, f"No se pudo abrir la descarga: {e}"

    def abrir_administrador_dispositivos(self) -> bool:
        """Abre el Administrador de dispositivos de Windows."""
        if not _es_windows():
            return False
        try:
            subprocess.Popen(["devmgmt.msc"], shell=True)
            return True
        except Exception as e:
            logger.error(f"Error abriendo Administrador de dispositivos: {e}")
            return False
