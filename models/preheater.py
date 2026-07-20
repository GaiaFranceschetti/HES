# =============================================================================
# models/preheater.py — Modello del preheater ad induzione
# =============================================================================
# Contiene:
#   - PreheaterSteadyState : calcoli di sizing (Layer 1)
#   - PreheaterDynamic     : simulazione con rampa accensione (Layer 2)
# =============================================================================

import numpy as np
from config import AIR, PREHEATER, FURNACE, GAS


class PreheaterSteadyState:
    """
    Modello stazionario del preheater ad induzione.
    """

    def __init__(self):
        self.eta_ind   = PREHEATER["eta_ind"]
        self.P_el_max  = PREHEATER["P_el_max"]
        self.T_in      = AIR["T_in"]
        self.T_air_out = PREHEATER["T_air_out_target"]
        self.delta_T   = PREHEATER["delta_T_target"]
        self.m_dot     = AIR["m_dot"]
        self.cp        = AIR["cp"]
        self.LHV       = GAS["LHV"] * 1e6
        self.eta_furn  = FURNACE["eta_furnace"]

    def run(self, P_el_kw: float) -> dict:
        Q_ind    = self.eta_ind * P_el_kw * 1000
        Q_target = self.m_dot * self.cp * self.delta_T
        Q_reale  = min(Q_ind, Q_target)
        T_air_out = self.T_in + Q_reale / (self.m_dot * self.cp)
        delta_mgas = Q_reale / (self.LHV * self.eta_furn)
        delta_mgas_kgh = delta_mgas * 3600
        LHV_kWh_per_kg = GAS["LHV"] / 3.6
        gas_savings_eur_h = delta_mgas * LHV_kWh_per_kg * GAS["price"] * 3600

        return {
            "P_el_kw":           P_el_kw,
            "Q_ind_kw":          Q_ind / 1000,
            "Q_target_kw":       Q_target / 1000,
            "Q_reale_kw":        Q_reale / 1000,
            "T_air_in":          self.T_in,
            "T_air_out":         T_air_out,
            "delta_T_air":       T_air_out - self.T_in,
            "delta_mgas_kgh":    delta_mgas_kgh,
            "gas_savings_eur_h": gas_savings_eur_h,
        }

    def sizing_curve(self, P_range_kw=None):
        if P_range_kw is None:
            P_range_kw = np.linspace(0, self.P_el_max, 50)
        return [self.run(P) for P in P_range_kw]