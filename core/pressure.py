"""Nonnegative normal LINE load (N/m), never pressure in Pa."""
import numpy as np

FAMILIES = ("uniform", "trapezoid", "quartic")

def quadrature_weights(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or len(x) < 3 or not np.isfinite(x).all() or np.any(np.diff(x) <= 0):
        raise ValueError("Grid must be finite, strictly increasing, with >=3 nodes")
    w = np.empty_like(x)
    w[0], w[-1] = (x[1]-x[0])/2, (x[-1]-x[-2])/2
    w[1:-1] = (x[2:]-x[:-2])/2
    return w

def shape(u, family="trapezoid", left=0.134, right=0.707):
    u = np.asarray(u, dtype=float)
    if not np.isfinite(u).all() or np.any((u < 0) | (u > 1)):
        raise ValueError("Normalized coordinate must lie in [0,1]")
    if family == "uniform":
        return np.ones_like(u)
    if family == "trapezoid":
        if not (0 < left < right < 1):
            raise ValueError("Require 0 < left < right < 1")
        h = np.where(u < left, u/left, np.where(u <= right, 1., (1-u)/(1-right)))
        return h * 2/(1+right-left)
    if family == "quartic":
        return 30*u*u*(1-u)**2  # Beta(3,3), integral exactly one
    raise ValueError(f"Unknown pressure family: {family}")

def line_load(x, L, Fz, family="trapezoid", left=0.134, right=0.707):
    x = np.asarray(x, dtype=float)
    w = quadrature_weights(x)
    if not np.isfinite([L, Fz]).all() or L <= 0 or Fz <= 0:
        raise ValueError("L and contact load Fz must be positive; contact loss is out of domain")
    if abs(x[0]) > 1e-14 or abs(x[-1]-L) > 1e-12:
        raise ValueError("Grid must include both 0 and L")
    raw = shape(x/L, family, left, right)
    area = w @ raw
    if area <= 0:
        raise ValueError("Grid does not resolve the pressure shape")
    p = Fz*raw/area
    return p, {"raw_integral_relative_error": float(area/L-1),
               "normalization_factor": float(L/area),
               "load_relative_error": float((w@p)/Fz-1),
               "centroid_m": float(w@(p*x)/Fz)}