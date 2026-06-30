"""Simple Incoterms cost helper."""

from __future__ import annotations


def incoterms_costs(exw: float, inland: float = 0, port: float = 0, freight: float = 0, insurance: float = 0) -> dict:
    fob = exw + inland + port
    cif = fob + freight + insurance
    return {"EXW": round(exw, 2), "FOB": round(fob, 2), "CIF": round(cif, 2)}
