# -*- coding: utf-8 -*-
"""
Perfil del Renault Duster — vehículo de prueba principal del proyecto.

El Duster (Dacia Duster en Europa) usa la plataforma B0/H79 de Renault.
Produción: 2010–presente (1ª gen hasta 2017, 2ª gen desde 2018).

Motorizaciones comunes en Latinoamérica:
  - 1.6 SCe 16V (H4M) — gasolina, 110/114 CV → ECU Bosch ME17.9.x
  - 2.0 16V (F4R) — gasolina, 138 CV → ECU Bosch ME7.4.6 / Valeo V42
  - 1.5 dCi (K9K) — diesel, 85/90/110 CV → ECU Bosch EDC17C11 / Delphi DCM3.4
  - 4WD disponible en versiones medianas/altas
"""
from typing import Dict, List, Optional
from .addresses import MODULOS_RENAULT, MODULOS_PRINCIPALES, ModuloECU
from .pids import PIDS_MOTOR_RENAULT, PIDS_CAJA


class PerfilDuster:
    """
    Perfil de diagnóstico específico del Renault Duster.
    Contiene configuración, módulos conocidos y rutinas especiales.
    """

    NOMBRE = "Renault Duster"
    PLATAFORMA = "B0/H79"
    PROTOCOLO_CAN = "ISO 15765-4 CAN 500kbps 11-bit"
    CODIGO_ELM327_PROTOCOLO = "6"  # ATSP6

    # Variantes de motor y su ECU correspondiente
    VARIANTES_MOTOR = {
        "1.6 SCe H4M": {
            "ecu": "Bosch ME17.9.x / ME17.9.20",
            "combustible": "gasolina",
            "turbo": False,
            "dpf": False,
            "cilindros": 4,
        },
        "2.0 F4R": {
            "ecu": "Bosch ME7.4.6 / Valeo V42",
            "combustible": "gasolina",
            "turbo": False,
            "dpf": False,
            "cilindros": 4,
        },
        "1.5 dCi K9K": {
            "ecu": "Bosch EDC17C11 / Delphi DCM3.4 / DCM6.2",
            "combustible": "diesel",
            "turbo": True,
            "dpf": True,  # Depende del año — post-Euro5 tiene DPF
            "cilindros": 4,
        },
    }

    # Rutinas de servicio conocidas (UDS Servicio 0x31)
    RUTINAS_SERVICIO = {
        "reset_adaptaciones_motor": {
            "id_rutina": 0x0200,
            "descripcion": "Borra las adaptaciones aprendidas del motor (mezcla, idle, EGR)",
            "requiere_sesion_extendida": True,
        },
        "reset_adaptaciones_embrague": {
            "id_rutina": 0x0201,
            "descripcion": "Reinicia las adaptaciones del embrague EDC/automático",
            "requiere_sesion_extendida": True,
        },
        "prueba_inyectores": {
            "id_rutina": 0x0300,
            "descripcion": "Activa cada inyector individualmente para verificar funcionamiento",
            "requiere_sesion_extendida": True,
        },
        "reset_dpf": {
            "id_rutina": 0x0400,
            "descripcion": "Reinicia el contador de saturación del filtro DPF",
            "requiere_sesion_extendida": True,
        },
        "regeneracion_forzada_dpf": {
            "id_rutina": 0x0401,
            "descripcion": "Inicia regeneración forzada del filtro DPF en estático",
            "requiere_sesion_extendida": True,
        },
        "calibracion_angulo_volante": {
            "id_rutina": 0x0500,
            "descripcion": "Calibra el sensor de ángulo del volante (necesario tras cambio)",
            "requiere_sesion_extendida": True,
        },
        "reset_luces_servicio": {
            "id_rutina": 0x0600,
            "descripcion": "Apaga el indicador de mantenimiento (cambio de aceite)",
            "requiere_sesion_extendida": False,
        },
    }

    # Actuadores controlables (UDS Servicio 0x2F)
    ACTUADORES = {
        "ventilador_cooling": {
            "did": 0x0500,
            "descripcion": "Activa el ventilador del radiador para prueba",
            "unidad": "on/off",
        },
        "compresor_ac": {
            "did": 0x0501,
            "descripcion": "Activa el compresor del aire acondicionado",
            "unidad": "on/off",
        },
        "bomba_combustible": {
            "did": 0x0502,
            "descripcion": "Activa la bomba de combustible para prueba",
            "unidad": "on/off",
        },
        "valvula_egr": {
            "did": 0x0503,
            "descripcion": "Controla apertura de la válvula EGR (0-100%)",
            "unidad": "%",
        },
        "turbo_vgt": {
            "did": 0x0504,
            "descripcion": "Controla posición del turbo VGT (solo K9K diesel)",
            "unidad": "%",
        },
        "inyector_1": {
            "did": 0x0510,
            "descripcion": "Activa inyector #1 para prueba individual",
            "unidad": "on/off",
        },
        "inyector_2": {
            "did": 0x0511,
            "descripcion": "Activa inyector #2 para prueba individual",
            "unidad": "on/off",
        },
        "inyector_3": {
            "did": 0x0512,
            "descripcion": "Activa inyector #3 para prueba individual",
            "unidad": "on/off",
        },
        "inyector_4": {
            "did": 0x0513,
            "descripcion": "Activa inyector #4 para prueba individual",
            "unidad": "on/off",
        },
    }

    @classmethod
    def modulos(cls) -> List[ModuloECU]:
        """Retorna la lista de módulos ECU disponibles en el Duster."""
        return MODULOS_RENAULT

    @classmethod
    def modulos_principales(cls) -> List[ModuloECU]:
        """Solo los módulos más relevantes para diagnóstico inicial."""
        return MODULOS_PRINCIPALES

    @classmethod
    def pids_motor(cls) -> Dict:
        return PIDS_MOTOR_RENAULT

    @classmethod
    def pids_caja(cls) -> Dict:
        return PIDS_CAJA

    @classmethod
    def describir_motor(cls, variante: str) -> Optional[Dict]:
        return cls.VARIANTES_MOTOR.get(variante)

    @classmethod
    def rutinas_disponibles(cls) -> Dict:
        return cls.RUTINAS_SERVICIO

    @classmethod
    def actuadores_disponibles(cls) -> Dict:
        return cls.ACTUADORES

    @classmethod
    def resumen(cls) -> str:
        """Descripción técnica completa del vehículo."""
        return f"""
╔══════════════════════════════════════════════════════════════╗
║           PERFIL: {cls.NOMBRE:<42}║
╠══════════════════════════════════════════════════════════════╣
║  Plataforma  : {cls.PLATAFORMA:<46}║
║  Protocolo   : {cls.PROTOCOLO_CAN:<46}║
║  Código ELM  : ATSP{cls.CODIGO_ELM327_PROTOCOLO:<47}║
╠══════════════════════════════════════════════════════════════╣
║  MÓDULOS CONOCIDOS ({len(MODULOS_RENAULT)} total):
{"".join(f"║    • {m.nombre:<10} → 0x{m.id_solicitud:03X}/0x{m.id_respuesta:03X}  {m.descripcion[:35]:<35}║{chr(10)}" for m in MODULOS_RENAULT[:8])}╠══════════════════════════════════════════════════════════════╣
║  MOTORIZACIONES:
{"".join(f"║    • {nombre:<55}║{chr(10)}" for nombre in cls.VARIANTES_MOTOR)}╚══════════════════════════════════════════════════════════════╝
""".strip()
