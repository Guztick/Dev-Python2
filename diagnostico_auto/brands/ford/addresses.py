# -*- coding: utf-8 -*-
"""Módulos ECU Ford/Lincoln con protocolo CAN."""
from ..renault.addresses import ModuloECU

# Ford usa HS-CAN (500kbps) para powertrain y MS-CAN (125kbps) para carrocería
# El acceso desde OBD-II puerto usa principalmente HS-CAN

MODULOS_FORD = [
    ModuloECU(0x7E0, 0x7E8, "PCM",    "Módulo de control de tren de potencia", 1),
    ModuloECU(0x7E1, 0x7E9, "TCM",    "Módulo de control de transmisión", 1),
    ModuloECU(0x726, 0x72E, "ABS",    "Módulo ABS/AdvanceTrac", 1),
    ModuloECU(0x727, 0x72F, "RCM",    "Módulo de control de restraint — airbags", 1),
    ModuloECU(0x714, 0x71C, "BCM",    "Módulo de control de carrocería", 2),
    ModuloECU(0x720, 0x728, "IC",     "Cuadro de instrumentos", 2),
    ModuloECU(0x733, 0x73B, "OCSM",   "Módulo de clasificación del asiento del ocupante", 3),
    ModuloECU(0x7DF, 0x7DF, "OBD2",   "Dirección funcional OBD-II", 1),
]
