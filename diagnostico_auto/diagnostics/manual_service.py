# -*- coding: utf-8 -*-
"""
Servicio de manuales de taller para Renault Duster.

Carga procedimientos de diagnóstico, información de sistemas y
valores de referencia desde la base de datos JSON. Proporciona
la interfaz entre los DTCs detectados y los procedimientos guiados.
"""
import json
import os
from dataclasses import dataclass, field
from typing import Optional

_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "database", "manuales")


def _cargar(nombre_archivo: str) -> dict:
    ruta = os.path.join(_BASE, nombre_archivo)
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@dataclass
class PasoProc:
    num: int
    titulo: str
    detalle: str
    herramienta: str
    imagen: Optional[str] = None

    def ruta_imagen(self) -> Optional[str]:
        if not self.imagen:
            return None
        ruta = os.path.join(_BASE, "images", self.imagen)
        return ruta if os.path.exists(ruta) else None


@dataclass
class Procedimiento:
    codigo_dtc: str
    titulo: str
    sistema: str
    motores: list
    icono: str
    color_severidad: str
    sintomas: list
    componentes: list
    valores_referencia: dict
    pasos: list[PasoProc]

    @classmethod
    def desde_dict(cls, codigo: str, datos: dict) -> "Procedimiento":
        pasos = [
            PasoProc(
                num=p["num"],
                titulo=p["titulo"],
                detalle=p["detalle"],
                herramienta=p.get("herramienta", ""),
                imagen=p.get("imagen"),
            )
            for p in datos.get("pasos", [])
        ]
        return cls(
            codigo_dtc=codigo,
            titulo=datos.get("titulo", ""),
            sistema=datos.get("sistema", ""),
            motores=datos.get("motor", []),
            icono=datos.get("icono", "wrench"),
            color_severidad=datos.get("color_severidad", "advertencia"),
            sintomas=datos.get("sintomas_tipicos", []),
            componentes=datos.get("componentes_involucrados", []),
            valores_referencia=datos.get("valores_referencia", {}),
            pasos=pasos,
        )

    @property
    def num_pasos(self) -> int:
        return len(self.pasos)


@dataclass
class ComponenteSistema:
    id: str
    nombre: str
    ubicacion: str
    descripcion: str
    par_apriete: Optional[str]
    herramienta_especial: Optional[str]


@dataclass
class Sistema:
    id: str
    nombre: str
    descripcion: str
    icono: str
    componentes: list[ComponenteSistema]
    especificaciones: dict

    @classmethod
    def desde_dict(cls, id_sistema: str, datos: dict) -> "Sistema":
        comps = [
            ComponenteSistema(
                id=c.get("id", ""),
                nombre=c.get("nombre", ""),
                ubicacion=c.get("ubicacion", ""),
                descripcion=c.get("descripcion", ""),
                par_apriete=c.get("par_apriete"),
                herramienta_especial=c.get("herramienta_especial"),
            )
            for c in datos.get("componentes", [])
        ]
        return cls(
            id=id_sistema,
            nombre=datos.get("nombre", id_sistema),
            descripcion=datos.get("descripcion", ""),
            icono=datos.get("icono", "cog"),
            componentes=comps,
            especificaciones=datos.get("especificaciones", {}),
        )


@dataclass
class GrupoPIDs:
    nombre: str
    pids: list[dict]


class ServicioManual:
    """
    Punto de acceso único a la base de datos de manuales.
    Singleton cargado una sola vez.
    """
    _instancia: Optional["ServicioManual"] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self):
        raw_proc = _cargar("procedimientos_duster.json")
        raw_sis = _cargar("sistemas_duster.json")
        raw_ref = _cargar("valores_referencia_duster.json")

        self._procedimientos: dict[str, Procedimiento] = {
            codigo: Procedimiento.desde_dict(codigo, datos)
            for codigo, datos in raw_proc.get("procedimientos", {}).items()
        }

        self._sistemas: dict[str, Sistema] = {
            id_sis: Sistema.desde_dict(id_sis, datos)
            for id_sis, datos in raw_sis.get("sistemas", {}).items()
        }

        self._grupos_ref: dict[str, GrupoPIDs] = {
            gid: GrupoPIDs(
                nombre=g.get("nombre", gid),
                pids=g.get("pids", []),
            )
            for gid, g in raw_ref.get("grupos", {}).items()
        }

    # ---------- Procedimientos ----------

    def procedimiento(self, codigo_dtc: str) -> Optional[Procedimiento]:
        """Retorna el procedimiento para un DTC, o None si no existe."""
        return self._procedimientos.get(codigo_dtc.upper())

    def tiene_procedimiento(self, codigo_dtc: str) -> bool:
        return codigo_dtc.upper() in self._procedimientos

    def todos_los_procedimientos(self) -> list[Procedimiento]:
        return list(self._procedimientos.values())

    def buscar_procedimientos(self, termino: str) -> list[Procedimiento]:
        t = termino.lower()
        return [
            p for p in self._procedimientos.values()
            if t in p.titulo.lower()
            or t in p.sistema.lower()
            or t in p.codigo_dtc.lower()
        ]

    def procedimientos_por_sistema(self, sistema: str) -> list[Procedimiento]:
        s = sistema.lower()
        return [p for p in self._procedimientos.values()
                if s in p.sistema.lower()]

    # ---------- Sistemas / Despiece ----------

    def sistema(self, id_sistema: str) -> Optional[Sistema]:
        return self._sistemas.get(id_sistema)

    def todos_los_sistemas(self) -> list[Sistema]:
        return list(self._sistemas.values())

    # ---------- Valores de referencia ----------

    def grupos_referencia(self) -> list[GrupoPIDs]:
        return list(self._grupos_ref.values())

    def grupo_referencia(self, id_grupo: str) -> Optional[GrupoPIDs]:
        return self._grupos_ref.get(id_grupo)

    # ---------- Estadísticas ----------

    def estadisticas(self) -> dict:
        total_pasos = sum(p.num_pasos for p in self._procedimientos.values())
        total_comps = sum(len(s.componentes) for s in self._sistemas.values())
        return {
            "procedimientos": len(self._procedimientos),
            "pasos_totales": total_pasos,
            "sistemas": len(self._sistemas),
            "componentes_total": total_comps,
            "grupos_referencia": len(self._grupos_ref),
        }


# Instancia global
servicio_manual = ServicioManual()
