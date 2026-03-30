from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np


START_TYPES = {
    1: "Successful start",
    2: "Successful start with alarm",
    3: "RotorProtek tripped start",
    4: "Externally aborted start",
    5: "Start longer than two minutes",
}

PROTECTIONS = {
    0: "Not protected",
    1: "Factory acceptance tests",
    2: "Cold commissioning start",
    3: "Hot commissioning start",
    4: "Start previous to maintenance",
    5: "Start after maintenance",
}

SCALAR_FIELDS = [
    "Duración (s)", "I máx (Arms)", "Tiempo I máx (s)", "I inicial", "I final",
    "Vel ini", "Vel fin", "Sampling rate (ms)", "% desequ. fases", "% d motores",
    "Temp ini (K)", "Temp fin (K)", "Par máx (%)", "Par mín (%)",
    "Par cort (%)", "Tiempo cort(s)", "R ini (Ω)", "R fin (Ω)",
    "Ratio R", "E dis(MJ)", "Amp frz(%)", "Inercia", "I cortoc (A)", "Ángulo (°)",
]

MULTI_START_SCALAR_FIELDS = [
    ("Duración (s)", 0.1),
    ("I máx (Arms)", 1.0),
    ("Tiempo I máx (s)", 0.1),
    ("I inicial", 1.0),
    ("I final", 1.0),
    ("Vel ini", 1.0),
    ("Vel fin", 1.0),
    ("Sampling rate (ms)", 1.0),
    ("% desequ. fases", 0.1),
    ("% d motores", 0.1),
    ("Temp ini (K)", 1.0),
    ("Temp fin (K)", 1.0),
    ("Par máx (%)", 0.1),
    ("Par mín (%)", 0.1),
    ("Par cort (%)", 0.1),
    ("Tiempo cort(s)", 0.1),
    ("R ini (Ω)", 0.001),
    ("R fin (Ω)", 0.001),
    ("Ratio R", 0.1),
    ("E dis(MJ)", 0.1),
    ("Amp frz(%)", 0.1),
    ("Inercia", 1.0),
    ("I cortoc (A)", 1.0),
    ("Ángulo (°)", 1.0),
]

SINGLE_START_REQUIRED_HEADERS = {
    "speedvstime(%syncspd)",
    "rotcurrentvstime(%in)",
    "mottorquevst(%flt)",
    "starttime(s)",
    "protection",
    "typeofstart",
    "time",
}

SINGLE_START_COLUMN_MAP = {
    "speedvstime(%syncspd)": "speed",
    "rotcurrentvstime(%in)": "current",
    "mottorquevst(%flt)": "torque",
    "secondmotcurrvst(%in)": "dual_current",
    "starttime(s)": "time",
    "loadtvsmillang(%flt)": "load_torque",
    "motortvsmillang(%flt)": "motor_torque",
    "frequency(hz)": "harmonic_freq",
    "harmonicamp(arms)": "harmonic_amp_arms",
    "harmonicamp(%irms)": "harmonic_amp_irms",
    "harmonicamp(%in)": "harmonic_amp_pct_nominal",
}

SINGLE_START_SCALAR_MAP = {
    "totalstrtngtime(s)": ("Duración (s)", 1.0, 0.0),
    "maxcurrent(arms)": ("I máx (Arms)", 1.0, 0.0),
    "tofmaxcurrent(s)": ("Tiempo I máx (s)", 1.0, 0.0),
    "initcurrent(arms)": ("I inicial", 1.0, 0.0),
    "finalcurrent(arms)": ("I final", 1.0, 0.0),
    "shortingspeed(rpm)": ("Vel ini", 1.0, 0.0),
    "finalspeed(rpm)": ("Vel fin", 1.0, 0.0),
    "samplerate(ms)": ("Sampling rate (ms)", 1.0, 0.0),
    "phasecurrunbalance(%in)": ("% desequ. fases", 1.0, 0.0),
    "motorscurrunbalance(%in)": ("% d motores", 1.0, 0.0),
    "initelecttemp(degc)": ("Temp ini (K)", 1.0, 273.15),
    "finalelecttemp(degc)": ("Temp fin (K)", 1.0, 273.15),
    "maxtorque(%flt)": ("Par máx (%)", 1.0, 0.0),
    "mintorque(%flt)": ("Par mín (%)", 1.0, 0.0),
    "torqueatshort(%flt)": ("Par cort (%)", 1.0, 0.0),
    "timeofshort(s)": ("Tiempo cort(s)", 1.0, 0.0),
    "initres(ohm)": ("R ini (Ω)", 1.0, 0.0),
    "finalres(ohm)": ("R fin (Ω)", 1.0, 0.0),
    "resratio": ("Ratio R", 1.0, 0.0),
    "energy(mj)": ("E dis(MJ)", 1.0, 0.0),
    "frzchrgamp(%flt)": ("Amp frz(%)", 1.0, 0.0),
    "inertia(kgm2)": ("Inercia", 1.0, 0.0),
    "maxshortcurr(a)": ("I cortoc (A)", 1.0, 0.0),
    "tumblingangle(deg)": ("Ángulo (°)", 1.0, 0.0),
}


@dataclass
class StartupSeries:
    speed: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    current: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    torque: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    time: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    load_torque: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    motor_torque: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    dual_current: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    harmonic_amp: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    harmonic_freq_raw: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    harmonic_freq_hz: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    def to_legacy(self) -> Dict[str, np.ndarray]:
        return {
            "speed": self.speed,
            "current": self.current,
            "torque": self.torque,
            "time": self.time,
            "load_torque": self.load_torque,
            "motor_torque": self.motor_torque,
            "dual_current": self.dual_current,
            "harmonic_amp": self.harmonic_amp,
            "harmonic_freq_raw": self.harmonic_freq_raw,
            "harmonic_freq_hz": self.harmonic_freq_hz,
        }


@dataclass
class StartupRecord:
    label: str
    timestamp_text: str
    timestamp_dt: Optional[datetime]
    protection: str
    start_type: str
    description: str
    scalars: Dict[str, float]
    series: StartupSeries
    source_kind: str

    def to_legacy(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "timestamp_text": self.timestamp_text,
            "timestamp_dt": self.timestamp_dt,
            "protection": self.protection,
            "start_type": self.start_type,
            "description": self.description,
            "scalars": dict(self.scalars),
            "series": self.series.to_legacy(),
            "source_kind": self.source_kind,
        }


@dataclass
class StartupDataset:
    csv_type: Optional[str]
    view_mode: str
    records: List[StartupRecord]
    validation_issues: List[str] = field(default_factory=list)

    def to_legacy_records(self) -> List[Dict[str, object]]:
        return [record.to_legacy() for record in self.records]
