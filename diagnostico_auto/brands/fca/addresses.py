# -*- coding: utf-8 -*-
"""Módulos ECU FCA — Chrysler/Dodge/Jeep/Ram con protocolo CAN."""
from ..renault.addresses import ModuloECU

# FCA usa principalmente UDS sobre CAN, similar al estándar europeo
# Desde 2013 la mayoría de vehículos FCA usan UDS completo

MODULOS_FCA = [
    ModuloECU(0x7E0, 0x7E8, "PCM",    "Módulo de control de tren de potencia", 1),
    ModuloECU(0x7E1, 0x7E9, "TCM",    "Módulo de control de transmisión", 1),
    ModuloECU(0x7A8, 0x7B0, "BCM",    "Módulo de control de carrocería", 2),
    ModuloECU(0x7E4, 0x7EC, "ABS",    "Sistema de frenos antibloqueo y ESP", 1),
    ModuloECU(0x7E8, 0x7F0, "AIRBAG", "Módulo de airbags y cinturones", 1),
    ModuloECU(0x7A0, 0x7A8, "HVAC",   "Control de climatización", 3),
    ModuloECU(0x7C0, 0x7C8, "IC",     "Cuadro de instrumentos", 2),
    ModuloECU(0x7DF, 0x7DF, "OBD2",   "Dirección funcional OBD-II", 1),
]
