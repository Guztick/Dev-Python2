# -*- coding: utf-8 -*-
"""Módulos ECU GM/Chevrolet con protocolo GMLAN (CAN)."""
from ..renault.addresses import ModuloECU

# GM usa direcciones CAN diferentes a Renault pero el mismo formato UDS/OBD-II
# HS-CAN (High Speed, 500kbps) — motor y transmisión
# MS-CAN (Medium Speed, 33.3kbps) — carrocería (requiere adaptador especial)

MODULOS_GM = [
    ModuloECU(0x7E0, 0x7E8, "PCM",    "Módulo de control de tren de potencia (motor + transmisión)", 1),
    ModuloECU(0x7E1, 0x7E9, "TCM",    "Módulo de control de transmisión automática", 1),
    ModuloECU(0x7A0, 0x7A8, "BCM",    "Módulo de control de carrocería (luces, puertas, alarma)", 2),
    ModuloECU(0x760, 0x768, "EBCM",   "Módulo de control de frenos eléctricos (ABS/StabiliTrak)", 1),
    ModuloECU(0x780, 0x788, "SDM",    "Módulo de diagnóstico de restraint — airbags", 1),
    ModuloECU(0x740, 0x748, "HVAC",   "Módulo de control de climatización", 3),
    ModuloECU(0x720, 0x728, "IPC",    "Centro de información del conductor (cuadro)", 2),
    ModuloECU(0x7DF, 0x7DF, "OBD2",   "Dirección funcional OBD-II (todos los módulos)", 1),
]
