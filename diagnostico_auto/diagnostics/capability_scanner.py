# -*- coding: utf-8 -*-
"""
Escáner de capacidades — el módulo central del proyecto.

Esta es la característica diferenciadora de la herramienta: determinar
EXACTAMENTE qué puede hacer con cada ECU del vehículo conectado.

El proceso de escaneo:
  1. Detectar protocolo de comunicación del vehículo
  2. Encontrar qué módulos ECU están presentes en el bus CAN
  3. Para cada módulo, determinar:
     a. Qué servicios OBD-II responde
     b. Qué servicios UDS están disponibles
     c. Qué nivel de acceso se puede obtener
     d. Qué datos/actuadores/rutinas se pueden usar
  4. Construir un reporte de capacidades con todas las opciones disponibles
"""
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from core.hardware.elm327 import ELM327
from core.protocols.obd2 import OBD2
from core.protocols.uds import UDS, Servicio

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estructura de resultados
# ---------------------------------------------------------------------------

@dataclass
class NivelAcceso:
    """Nivel de acceso que se pudo establecer con un ECU."""
    obd2_basico: bool = False          # OBD-II modo 01-0A estándar
    uds_default: bool = False          # Sesión UDS default (0x01)
    uds_extendido: bool = False        # Sesión UDS extendida (0x03)
    uds_seguro: bool = False           # UDS con Security Access desbloqueado
    uds_programacion: bool = False     # Sesión de programación (0x02)

    def descripcion(self) -> str:
        if self.uds_seguro:
            return "Acceso completo (Nivel 4) — Datos, actuadores y rutinas disponibles"
        if self.uds_extendido:
            return "Acceso extendido (Nivel 3) — Datos avanzados y algunas rutinas"
        if self.uds_default:
            return "Acceso UDS básico (Nivel 2) — Identificación y DTCs avanzados"
        if self.obd2_basico:
            return "Acceso OBD-II estándar (Nivel 1) — Datos básicos y DTCs genéricos"
        return "Sin acceso"


@dataclass
class CapacidadECU:
    """Capacidades detectadas de un módulo ECU específico."""
    nombre: str
    descripcion: str
    id_solicitud: int
    id_respuesta: int
    presente: bool = False
    nivel_acceso: NivelAcceso = field(default_factory=NivelAcceso)

    # Capacidades específicas detectadas
    servicios_uds: List[int] = field(default_factory=list)
    pids_obd2: List[int] = field(default_factory=list)
    dids_leibles: List[int] = field(default_factory=list)
    num_dtcs: int = 0
    soporta_actuadores: bool = False
    soporta_rutinas: bool = False
    soporta_escritura: bool = False

    # Información del ECU
    vin: Optional[str] = None
    numero_parte: Optional[str] = None
    version_software: Optional[str] = None

    def resumen_capacidades(self) -> List[str]:
        """Retorna lista de capacidades disponibles en lenguaje natural."""
        capacidades = []

        if self.nivel_acceso.obd2_basico:
            capacidades.append(f"✅ Leer datos en tiempo real ({len(self.pids_obd2)} PIDs disponibles)")
            capacidades.append("✅ Leer DTCs estándar OBD-II")
            capacidades.append("✅ Leer VIN e información del vehículo")

        if self.nivel_acceso.uds_default or self.nivel_acceso.uds_extendido:
            capacidades.append(f"✅ Leer información del ECU ({len(self.dids_leibles)} datos disponibles)")
            if self.num_dtcs >= 0:
                capacidades.append(f"✅ Leer DTCs avanzados (UDS) — {self.num_dtcs} código(s) encontrado(s)")
            capacidades.append("✅ Borrar DTCs avanzados")

        if self.nivel_acceso.uds_extendido:
            if self.soporta_rutinas:
                capacidades.append("✅ Ejecutar rutinas de diagnóstico y servicio")
            if self.soporta_actuadores:
                capacidades.append("✅ Controlar actuadores para pruebas")

        if self.nivel_acceso.uds_seguro:
            if self.soporta_escritura:
                capacidades.append("✅ Escribir parámetros de calibración")
            capacidades.append("✅ Reset de adaptaciones aprendidas")

        if not capacidades:
            capacidades.append("❌ Módulo no responde o sin acceso disponible")

        return capacidades


@dataclass
class ReporteEscaneo:
    """Resultado completo del escaneo de capacidades del vehículo."""
    protocolo_detectado: Optional[str] = None
    voltaje_bateria: Optional[float] = None
    vin: Optional[str] = None
    modulos: List[CapacidadECU] = field(default_factory=list)
    tiempo_escaneo: float = 0.0
    errores: List[str] = field(default_factory=list)

    @property
    def modulos_presentes(self) -> List[CapacidadECU]:
        return [m for m in self.modulos if m.presente]

    @property
    def total_dtcs(self) -> int:
        return sum(m.num_dtcs for m in self.modulos_presentes)

    def imprimir(self) -> None:
        print("\n" + "═" * 65)
        print("  REPORTE DE CAPACIDADES DEL VEHÍCULO")
        print("═" * 65)
        print(f"  Protocolo  : {self.protocolo_detectado or 'No detectado'}")
        print(f"  Batería    : {self.voltaje_bateria:.1f}V" if self.voltaje_bateria else "  Batería    : N/D")
        print(f"  VIN        : {self.vin or 'No disponible'}")
        print(f"  DTCs total : {self.total_dtcs}")
        print(f"  Tiempo     : {self.tiempo_escaneo:.1f}s")
        print("─" * 65)

        for modulo in self.modulos_presentes:
            print(f"\n  📦 {modulo.nombre} — {modulo.descripcion}")
            print(f"     Dirección: 0x{modulo.id_solicitud:03X} → 0x{modulo.id_respuesta:03X}")
            print(f"     Acceso:    {modulo.nivel_acceso.descripcion()}")
            if modulo.numero_parte:
                print(f"     Parte:     {modulo.numero_parte}")
            if modulo.version_software:
                print(f"     Software:  {modulo.version_software}")
            print("     Capacidades disponibles:")
            for cap in modulo.resumen_capacidades():
                print(f"       {cap}")

        print("\n" + "═" * 65)


# ---------------------------------------------------------------------------
# Escáner principal
# ---------------------------------------------------------------------------

class EscanerCapacidades:
    """
    Escanea un vehículo y determina todas las capacidades de diagnóstico
    disponibles en cada módulo ECU conectado al bus CAN.
    """

    def __init__(self, adaptador: ELM327, callback_progreso: Optional[Callable] = None):
        """
        callback_progreso: función(texto, porcentaje) para actualizar UI.
        """
        self._elm = adaptador
        self._callback = callback_progreso or (lambda msg, pct: print(f"[{pct:3.0f}%] {msg}"))

    def _progreso(self, mensaje: str, porcentaje: float) -> None:
        self._callback(mensaje, porcentaje)

    def escanear_vehiculo(self, modulos_a_probar: List) -> ReporteEscaneo:
        """
        Ejecuta un escaneo completo del vehículo.
        modulos_a_probar: lista de ModuloECU de la marca correspondiente.
        """
        reporte = ReporteEscaneo()
        inicio = time.time()

        # Paso 1 — Conexión y protocolo
        self._progreso("Detectando protocolo del vehículo...", 5)
        reporte.voltaje_bateria = self._elm.leer_voltage_bateria()
        protocolo = self._elm.detectar_protocolo_vehiculo()
        reporte.protocolo_detectado = protocolo

        if not protocolo:
            reporte.errores.append("No se pudo establecer comunicación con el vehículo.")
            return reporte

        self._progreso(f"Protocolo: {protocolo}", 10)

        # Paso 2 — VIN por OBD-II estándar
        self._progreso("Leyendo VIN del vehículo...", 12)
        obd = OBD2(self._elm)
        reporte.vin = obd.leer_vin()

        # Paso 3 — Escanear cada módulo
        total_modulos = len(modulos_a_probar)
        for idx, definicion_modulo in enumerate(modulos_a_probar):
            porcentaje_base = 15 + (idx / total_modulos) * 80
            self._progreso(
                f"Probando {definicion_modulo.nombre} (0x{definicion_modulo.id_solicitud:03X})...",
                porcentaje_base,
            )

            capacidad = self._escanear_modulo(definicion_modulo, porcentaje_base)
            reporte.modulos.append(capacidad)

            if capacidad.presente:
                self._progreso(
                    f"✅ {definicion_modulo.nombre} encontrado — {capacidad.nivel_acceso.descripcion()}",
                    porcentaje_base + 1,
                )
            else:
                logger.debug(f"{definicion_modulo.nombre} no responde.")

        reporte.tiempo_escaneo = time.time() - inicio
        self._progreso("Escaneo completo.", 100)
        return reporte

    def _escanear_modulo(self, definicion, pct_base: float) -> CapacidadECU:
        """Escanea un módulo ECU individual y determina sus capacidades."""
        capacidad = CapacidadECU(
            nombre=definicion.nombre,
            descripcion=definicion.descripcion,
            id_solicitud=definicion.id_solicitud,
            id_respuesta=definicion.id_respuesta,
        )

        # Dirección funcional OBD-II — prueba diferente
        es_funcional = definicion.id_solicitud == 0x7DF
        if es_funcional:
            return self._escanear_obd2_funcional(capacidad)

        uds = UDS(self._elm, definicion.id_solicitud, definicion.id_respuesta)

        # ---- Nivel 1: ¿Responde a sesión UDS default? ----
        if not uds.abrir_sesion_default():
            # Si no responde a UDS default, puede ser que solo hable OBD-II
            # Intentamos OBD-II si el rango de dirección es el estándar motor
            if definicion.id_solicitud == 0x7E0:
                return self._escanear_con_obd2(capacidad)
            return capacidad  # Módulo no presente o no responde

        capacidad.presente = True
        capacidad.nivel_acceso.uds_default = True
        time.sleep(0.1)

        # ---- Leer información básica ----
        info = uds.leer_info_completa()
        capacidad.vin = info.get("VIN")
        capacidad.numero_parte = info.get("Número de parte")
        capacidad.version_software = info.get("Versión software")

        # ---- Leer DTCs UDS ----
        try:
            dtcs = uds.leer_dtcs()
            capacidad.num_dtcs = len(dtcs)
        except Exception:
            capacidad.num_dtcs = 0

        # ---- Nivel 2: ¿Acepta sesión extendida? ----
        time.sleep(0.1)
        if uds.abrir_sesion_extendida():
            capacidad.nivel_acceso.uds_extendido = True

            # Verificar soporte de rutinas (0x31)
            resp_rutina = self._elm.enviar_uds(
                definicion.id_solicitud, definicion.id_respuesta,
                Servicio.CONTROL_RUTINA, bytes([0x01, 0x00, 0x00]),
                timeout=1.5,
            )
            # NRC 0x11 = no soportado, cualquier otra respuesta (incluso 0x31) = soportado
            if resp_rutina:
                capacidad.soporta_rutinas = not (
                    len(resp_rutina) >= 3 and resp_rutina[2] == 0x11
                )

            # Verificar soporte de actuadores (0x2F)
            resp_io = self._elm.enviar_uds(
                definicion.id_solicitud, definicion.id_respuesta,
                Servicio.CONTROL_IO_COMPONENTE, bytes([0x00, 0x00, 0x00]),
                timeout=1.5,
            )
            if resp_io:
                capacidad.soporta_actuadores = not (
                    len(resp_io) >= 3 and resp_io[2] == 0x11
                )

            # Verificar soporte de escritura (0x2E)
            resp_write = self._elm.enviar_uds(
                definicion.id_solicitud, definicion.id_respuesta,
                Servicio.ESCRIBIR_DATO_POR_ID, bytes([0xF1, 0x90, 0x00]),
                timeout=1.5,
            )
            if resp_write:
                capacidad.soporta_escritura = not (
                    len(resp_write) >= 3 and resp_write[2] == 0x11
                )

        # ---- Nivel 3: ¿Acepta Security Access? ----
        # Solo intentamos solicitar el seed — no enviamos key (no la tenemos aún)
        time.sleep(0.1)
        seed = uds.solicitar_seed(nivel=0x01)
        if seed and len(seed) >= 2:
            # Si el ECU devuelve seed, el acceso de seguridad existe
            # (aunque no podamos desbloquearlo sin el algoritmo del fabricante)
            capacidad.nivel_acceso.uds_seguro = False  # Tenemos el seed pero no la key
            logger.info(f"ECU {definicion.nombre} requiere Security Access — seed obtenido")

        # Volver a sesión default para no interferir con otros módulos
        uds.abrir_sesion_default()

        return capacidad

    def _escanear_con_obd2(self, capacidad: CapacidadECU) -> CapacidadECU:
        """Escanea el ECU del motor usando OBD-II estándar."""
        obd = OBD2(self._elm)
        pids = obd.leer_pids_soportados(0x00)

        if not pids:
            return capacidad

        capacidad.presente = True
        capacidad.nivel_acceso.obd2_basico = True
        capacidad.pids_obd2 = pids

        # Leer más grupos de PIDs
        for grupo in [0x20, 0x40, 0x60]:
            pids_grupo = obd.leer_pids_soportados(grupo)
            capacidad.pids_obd2.extend(pids_grupo)

        # Leer DTCs OBD-II
        dtcs = obd.leer_dtcs()
        capacidad.num_dtcs = len(dtcs)

        return capacidad

    def _escanear_obd2_funcional(self, capacidad: CapacidadECU) -> CapacidadECU:
        """Prueba la dirección funcional OBD-II (0x7DF)."""
        obd = OBD2(self._elm)
        estado = obd.leer_estado_monitor()

        if estado:
            capacidad.presente = True
            capacidad.nivel_acceso.obd2_basico = True
            capacidad.num_dtcs = estado.get("num_dtcs", 0)

        return capacidad
