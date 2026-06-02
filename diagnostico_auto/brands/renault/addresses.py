# -*- coding: utf-8 -*-
"""
Mapa de direcciones CAN y módulos para vehículos Renault/Dacia.

Renault usa CAN bus con direccionamiento estándar UDS en la mayoría
de sus plataformas desde 2006. El Duster (plataforma B0/H79) sigue
el esquema Renault con algunas particularidades de la plataforma Dacia.

Formato de cada entrada:
  (ID_solicitud, ID_respuesta, nombre, descripción)
"""
from typing import NamedTuple, List


class ModuloECU(NamedTuple):
    id_solicitud: int    # CAN ID para enviar solicitudes al módulo
    id_respuesta: int    # CAN ID en el que responde el módulo
    nombre: str          # Nombre técnico del módulo
    descripcion: str     # Descripción en español
    prioridad: int       # 1=diagnóstico principal, 2=secundario, 3=auxiliar


# ---------------------------------------------------------------------------
# Módulos Renault/Dacia — Plataformas B, C, D (incluye Duster/Logan/Sandero)
# ---------------------------------------------------------------------------
MODULOS_RENAULT: List[ModuloECU] = [

    # ===== MOTOR / POWERTRAIN =====
    ModuloECU(0x7E0, 0x7E8, "UCE/PCM",
              "Unidad de Control del Motor (ECM/PCM) — motor + tren de potencia",
              prioridad=1),

    # ===== CAJA DE VELOCIDADES =====
    ModuloECU(0x7E1, 0x7E9, "TCM/EDC",
              "Módulo de Control de Transmisión — cajas automáticas/EDC/CVT",
              prioridad=1),

    # ===== CARROCERÍA / UCH =====
    ModuloECU(0x744, 0x764, "UCH",
              "Unidad Central de Habitáculo — luces, seguros, ventanas, alarma",
              prioridad=2),

    # ===== FRENOS ABS/ESP =====
    ModuloECU(0x760, 0x768, "ABS/ESP",
              "Sistema de frenos antibloqueo y control de estabilidad",
              prioridad=1),

    # ===== AIRBAG / SRS =====
    ModuloECU(0x752, 0x772, "AIRBAG",
              "Módulo de bolsas de aire y cinturones de seguridad",
              prioridad=1),

    # ===== DIRECCIÓN ASISTIDA ELÉCTRICA =====
    ModuloECU(0x76E, 0x76F, "EPS",
              "Dirección asistida eléctrica (columna de dirección)",
              prioridad=2),

    # ===== CLIMATIZACIÓN =====
    ModuloECU(0x7B0, 0x7B8, "HVAC",
              "Control de climatización y aire acondicionado",
              prioridad=3),

    # ===== CUADRO DE INSTRUMENTOS =====
    ModuloECU(0x743, 0x763, "CLUSTER",
              "Cuadro de instrumentos (velocímetro, tacómetro, indicadores)",
              prioridad=2),

    # ===== SENSOR DE LLUVIA/LUZ =====
    ModuloECU(0x745, 0x765, "UPC",
              "Unidad de preparación de carrocería — luces automáticas, limpiaparabrisas",
              prioridad=3),

    # ===== DIRECCIÓN ASISTIDA HIDRÁULICA ELECTRÓNICA =====
    ModuloECU(0x76B, 0x76C, "EPHS",
              "Dirección hidráulica asistida eléctricamente (bombas variables)",
              prioridad=3),

    # ===== MÓDULO BLUETOOTH/TELEMÁTICA =====
    ModuloECU(0x7A0, 0x7A8, "MULTIMEDIA",
              "Sistema multimedia, navegación, Bluetooth (si equipado)",
              prioridad=3),

    # ===== SISTEMA DE MONITOREO PRESIÓN NEUMÁTICOS =====
    ModuloECU(0x7A4, 0x7AC, "TPMS",
              "Sistema de monitoreo de presión de neumáticos",
              prioridad=3),

    # ===== INMOVILIZADOR =====
    ModuloECU(0x7A7, 0x7AF, "IMMO",
              "Inmovilizador de motor / transponder de llave",
              prioridad=2),

    # ===== CONTROL TECHO PANORÁMICO (si aplica) =====
    ModuloECU(0x7C6, 0x7CE, "SUNROOF",
              "Control de techo panorámico/solar (versiones equipadas)",
              prioridad=3),

    # ===== OBD ESTÁNDAR (funcional — todos los módulos) =====
    ModuloECU(0x7DF, 0x7DF, "OBD2_FUNCIONAL",
              "Dirección funcional OBD-II — transmite a TODOS los módulos simultáneamente",
              prioridad=1),
]

# Acceso rápido por nombre
MODULOS_POR_NOMBRE = {m.nombre: m for m in MODULOS_RENAULT}

# Módulos prioritarios para escaneo rápido
MODULOS_PRINCIPALES = [m for m in MODULOS_RENAULT if m.prioridad == 1]
