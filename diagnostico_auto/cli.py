# -*- coding: utf-8 -*-
"""
DiagnosticoPro — Herramienta de diagnóstico automotriz.

Punto de entrada del sistema. Para uso en desktop/pruebas.
La interfaz Android (Kivy) se lanzará desde gui/main_app.py.

Uso rápido en terminal:
    python main.py --wifi 192.168.0.10          # ELM327 WiFi
    python main.py --serial /dev/ttyUSB0         # ELM327 USB
    python main.py --demo                         # Modo demo sin hardware
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.hardware.base import ConexionWiFi, ConexionSerial
from core.hardware.elm327 import ELM327
from diagnostics.capability_scanner import EscanerCapacidades
from diagnostics.dtc_reader import LectorDTCs
from brands.renault.duster import PerfilDuster

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def menu_interactivo(elm: ELM327, modulos) -> None:
    """Menú de consola para diagnóstico interactivo."""
    lector = LectorDTCs(elm)

    while True:
        print("\n" + "═" * 55)
        print("  DIAGNÓSTICO PRO — Renault Duster")
        print("═" * 55)
        print("  1. Escanear capacidades del vehículo")
        print("  2. Leer códigos de falla (DTCs)")
        print("  3. Borrar códigos de falla")
        print("  4. Ver datos en tiempo real")
        print("  5. Información del vehículo (VIN, ECUs)")
        print("  0. Salir")
        print("─" * 55)

        opcion = input("  Selecciona una opción: ").strip()

        if opcion == "1":
            print("\nIniciando escaneo completo...")
            escaner = EscanerCapacidades(elm)
            reporte = escaner.escanear_vehiculo(PerfilDuster.modulos_principales())
            reporte.imprimir()

        elif opcion == "2":
            print("\nLeyendo códigos de falla...")
            dtcs = lector.leer_todos(modulos)
            print(lector.formatear_reporte(dtcs))

        elif opcion == "3":
            confirmar = input("⚠️  ¿Confirmas el borrado de TODOS los DTCs? (s/N): ")
            if confirmar.lower() == "s":
                resultados = lector.limpiar_todos(modulos)
                for modulo, exito in resultados.items():
                    estado = "✅" if exito else "❌"
                    print(f"  {estado} {modulo}")

        elif opcion == "4":
            from core.protocols.obd2 import OBD2, PIDS_ESTANDAR
            obd = OBD2(elm)
            print("\nDatos en tiempo real (Ctrl+C para detener):")
            try:
                while True:
                    for pid, defin in list(PIDS_ESTANDAR.items())[:8]:
                        resultado = obd.leer_pid(pid)
                        if resultado:
                            val, unidad, nombre = resultado
                            print(f"  {nombre:<40} {val:>8.1f} {unidad}")
                    print("─" * 55)
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nDetenido.")

        elif opcion == "5":
            from core.protocols.uds import UDS
            print("\nInformación de la ECU del motor:")
            uds = UDS(elm, 0x7E0, 0x7E8)
            info = uds.leer_info_completa()
            for clave, valor in info.items():
                print(f"  {clave:<25}: {valor or 'No disponible'}")

        elif opcion == "0":
            break
        else:
            print("  Opción no válida.")


def modo_demo() -> None:
    """Muestra el perfil del vehículo y la estructura sin hardware real."""
    print(PerfilDuster.resumen())
    print("\n✅ Modo demo — estructura del proyecto lista.")
    print("   Conecta un adaptador ELM327 para diagnóstico real.")


def main() -> None:
    parser = argparse.ArgumentParser(description="DiagnosticoPro — Diagnóstico automotriz")
    parser.add_argument("--wifi", metavar="IP", help="IP del adaptador ELM327 WiFi")
    parser.add_argument("--serial", metavar="PUERTO", help="Puerto serial del ELM327 USB")
    parser.add_argument("--demo", action="store_true", help="Modo demo sin hardware")
    parser.add_argument("--debug", action="store_true", help="Logging detallado")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        modo_demo()
        return

    # Establecer conexión
    if args.wifi:
        ip, _, puerto = args.wifi.partition(":")
        conexion = ConexionWiFi(host=ip, puerto=int(puerto) if puerto else 35000)
    elif args.serial:
        conexion = ConexionSerial(puerto=args.serial)
    else:
        print("Especifica --wifi <IP> o --serial <PUERTO>. Usa --demo para prueba sin hardware.")
        parser.print_help()
        sys.exit(1)

    elm = ELM327(conexion)
    print("Conectando al adaptador ELM327...")

    if not elm.conectar():
        print("❌ No se pudo conectar al adaptador.")
        sys.exit(1)

    print(f"✅ Conectado — {elm.version_elm}")
    print(f"   Protocolo: {elm.protocolo_activo}")
    voltaje = elm.leer_voltage_bateria()
    if voltaje:
        print(f"   Batería: {voltaje:.1f}V")

    try:
        modulos = PerfilDuster.modulos_principales()
        menu_interactivo(elm, modulos)
    finally:
        elm.desconectar()
        print("Desconectado.")


if __name__ == "__main__":
    main()
