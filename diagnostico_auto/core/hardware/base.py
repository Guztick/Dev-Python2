# -*- coding: utf-8 -*-
"""
Capa de abstracción de hardware para adaptadores OBD-II.
Define la interfaz base que todos los adaptadores deben implementar.
"""
from abc import ABC, abstractmethod
from typing import Optional


class ConexionBase(ABC):
    """Interfaz abstracta de conexión al adaptador."""

    @abstractmethod
    def conectar(self) -> bool:
        """Establece la conexión física. Retorna True si exitosa."""

    @abstractmethod
    def desconectar(self) -> None:
        """Cierra la conexión."""

    @abstractmethod
    def enviar_recibir(self, datos: str, timeout: float = 2.0) -> str:
        """Envía un comando y retorna la respuesta como texto."""

    @property
    @abstractmethod
    def conectado(self) -> bool:
        """True si la conexión está activa."""


class ConexionSerial(ConexionBase):
    """
    Conexión serial USB — para ELM327 por cable o pruebas en desktop.
    En Android no aplica directamente (usar ConexionBluetooth o WiFi).
    """

    def __init__(self, puerto: str, baudrate: int = 38400):
        self._puerto = puerto
        self._baudrate = baudrate
        self._serial = None

    def conectar(self) -> bool:
        import serial
        try:
            self._serial = serial.Serial(
                port=self._puerto,
                baudrate=self._baudrate,
                timeout=2.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            return self._serial.is_open
        except Exception as e:
            print(f"Error conexión serial: {e}")
            return False

    def desconectar(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def enviar_recibir(self, datos: str, timeout: float = 2.0) -> str:
        if not self._serial:
            return ""
        self._serial.timeout = timeout
        self._serial.write((datos + "\r").encode())
        respuesta = b""
        while True:
            byte = self._serial.read(1)
            if not byte or byte == b">":
                break
            respuesta += byte
        return respuesta.decode(errors="ignore").strip()

    @property
    def conectado(self) -> bool:
        return self._serial is not None and self._serial.is_open


class ConexionWiFi(ConexionBase):
    """
    Conexión TCP/IP — para ELM327 WiFi (192.168.0.10:35000 por defecto).
    Funciona perfectamente en Android con adaptadores WiFi.
    """

    def __init__(self, host: str = "192.168.0.10", puerto: int = 35000):
        self._host = host
        self._puerto = puerto
        self._socket = None

    def conectar(self) -> bool:
        import socket
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self._host, self._puerto))
            return True
        except Exception as e:
            print(f"Error conexión WiFi: {e}")
            self._socket = None
            return False

    def desconectar(self) -> None:
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._socket = None

    def enviar_recibir(self, datos: str, timeout: float = 2.0) -> str:
        if not self._socket:
            return ""
        try:
            self._socket.settimeout(timeout)
            self._socket.sendall((datos + "\r").encode())
            respuesta = b""
            while True:
                chunk = self._socket.recv(1024)
                if not chunk:
                    break
                respuesta += chunk
                if b">" in respuesta:
                    break
            return respuesta.decode(errors="ignore").replace(">", "").strip()
        except Exception:
            return ""

    @property
    def conectado(self) -> bool:
        return self._socket is not None


class ConexionBluetooth(ConexionBase):
    """
    Conexión Bluetooth RFCOMM — para ELM327 BT en Android.
    En desktop usa la librería 'bluetooth'. En Android usa Pyjnius.
    Implementación adaptativa según plataforma.
    """

    def __init__(self, direccion_mac: str, canal: int = 1):
        self._mac = direccion_mac
        self._canal = canal
        self._socket = None
        self._es_android = self._detectar_android()

    @staticmethod
    def _detectar_android() -> bool:
        try:
            import jnius  # noqa: F401
            return True
        except ImportError:
            return False

    def conectar(self) -> bool:
        if self._es_android:
            return self._conectar_android()
        return self._conectar_desktop()

    def _conectar_desktop(self) -> bool:
        try:
            import bluetooth
            self._socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._socket.connect((self._mac, self._canal))
            self._socket.settimeout(2.0)
            return True
        except Exception as e:
            print(f"Error BT desktop: {e}")
            return False

    def _conectar_android(self) -> bool:
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            BluetoothDevice = autoclass("android.bluetooth.BluetoothDevice")
            UUID = autoclass("java.util.UUID")
            adapter = BluetoothAdapter.getDefaultAdapter()
            device = adapter.getRemoteDevice(self._mac)
            uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            self._socket = device.createRfcommSocketToServiceRecord(uuid)
            self._socket.connect()
            return True
        except Exception as e:
            print(f"Error BT Android: {e}")
            return False

    def desconectar(self) -> None:
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._socket = None

    def enviar_recibir(self, datos: str, timeout: float = 2.0) -> str:
        if not self._socket:
            return ""
        try:
            if self._es_android:
                return self._io_android(datos, timeout)
            self._socket.settimeout(timeout)
            self._socket.send((datos + "\r").encode())
            respuesta = b""
            while True:
                byte = self._socket.recv(1)
                if not byte or byte == b">":
                    break
                respuesta += byte
            return respuesta.decode(errors="ignore").strip()
        except Exception:
            return ""

    def _io_android(self, datos: str, timeout: float) -> str:
        from jnius import autoclass
        InputStream = self._socket.getInputStream()
        OutputStream = self._socket.getOutputStream()
        cmd = (datos + "\r").encode()
        OutputStream.write(cmd)
        import time
        deadline = time.time() + timeout
        respuesta = b""
        while time.time() < deadline:
            if InputStream.available() > 0:
                byte = InputStream.read()
                if byte == ord(">"):
                    break
                respuesta += bytes([byte])
        return respuesta.decode(errors="ignore").strip()

    @property
    def conectado(self) -> bool:
        return self._socket is not None
