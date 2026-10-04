"""Parameter values have a single authority: parameter_registry.csv."""
from dataclasses import dataclass, replace
from pathlib import Path
import csv
import numpy as np

ROOT = Path(__file__).resolve().parent

def registry():
    with (ROOT / "parameter_registry.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["symbol"]: row for row in csv.DictReader(f)}

def value(symbol):
    return float(registry()[symbol]["value"])

@dataclass(frozen=True)
class TireParameters:
    L: float
    r: float
    sigma0_x: float
    sigma0_y: float
    sigma1_x: float
    sigma1_y: float
    sigma2: float
    mu_s: float
    mu_k: float
    v_s: float
    gamma: float
    pressure_left: float
    pressure_right: float
    Iw: float
    actuator_tau: float
    brake_max: float
    brake_rate: float

    @property
    def sigma0(self):
        return np.array([self.sigma0_x, self.sigma0_y])

    @property
    def sigma1(self):
        return np.array([self.sigma1_x, self.sigma1_y])

    def validate(self):
        if not np.isfinite(list(self.__dict__.values())).all():
            raise ValueError("Parameters must be finite")
        if min(self.L,self.r,self.sigma0_x,self.sigma0_y,self.mu_k,self.v_s,self.gamma,self.Iw,self.actuator_tau,self.brake_max,self.brake_rate) <= 0:
            raise ValueError("Positive physical coefficients required")
        if min(self.sigma1_x,self.sigma1_y,self.sigma2) < 0 or self.mu_s < self.mu_k:
            raise ValueError("Invalid friction/damping coefficients")
        if not 0 < self.pressure_left < self.pressure_right < 1:
            raise ValueError("Invalid pressure breakpoints")
        return self

def default_parameters(**overrides):
    rows = registry()
    p = TireParameters(**{k: float(rows[k]["value"]) for k in TireParameters.__dataclass_fields__})
    return replace(p, **overrides).validate()