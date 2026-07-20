# =============================================================================
# economics.py — Analisi economica
# =============================================================================

import numpy as np
from config import ECONOMICS


def simple_npv(annual_net_saving: float) -> float:
    """
    Calcola il Net Present Value (NPV) dell'investimento nel preheater.

    Formula:
        NPV = -CAPEX + Σ (saving_netto - OPEX) / (1+r)^t   per t = 1..N

    Parametri
    ---------
    annual_net_saving : float
        Risparmio netto annuo [€/anno] = risparmio gas - costo elettricità

    Ritorna
    -------
    float : NPV [€]
    """
    CAPEX    = ECONOMICS["CAPEX_preheater"]
    OPEX     = ECONOMICS["OPEX_annual"]
    r        = ECONOMICS["discount_rate"]
    N        = ECONOMICS["project_lifetime"]

    annual_cashflow = annual_net_saving - OPEX

    # Somma dei flussi di cassa attualizzati
    npv = -CAPEX
    for t in range(1, N + 1):
        npv += annual_cashflow / (1 + r) ** t

    return npv


def payback_period(annual_net_saving: float) -> float:
    """
    Calcola il periodo di ritorno semplice (Simple Payback Period).

    Formula: PBP = CAPEX / (saving_netto - OPEX)

    Parametri
    ---------
    annual_net_saving : float
        Risparmio netto annuo [€/anno]

    Ritorna
    -------
    float : Periodo di ritorno [anni]
    """
    CAPEX = ECONOMICS["CAPEX_preheater"]
    OPEX  = ECONOMICS["OPEX_annual"]

    annual_cashflow = annual_net_saving - OPEX
    if annual_cashflow <= 0:
        return float("inf")  # Non si ripaga mai

    return CAPEX / annual_cashflow


def lcoe_savings(annual_net_saving: float) -> dict:
    """
    Calcola i principali indicatori economici dell'investimento.

    Ritorna
    -------
    dict con NPV, PBP, IRR approssimato
    """
    npv = simple_npv(annual_net_saving)
    pbp = payback_period(annual_net_saving)

    return {
        "NPV_eur":          npv,
        "payback_anni":     pbp,
        "redditivo":        npv > 0,
    }


def sensitivity_analysis(annual_net_saving: float,
                          param: str,
                          values: list) -> list:
    """
    Analisi di sensibilità: varia un parametro economico e calcola NPV.

    Parametri
    ---------
    annual_net_saving : float
        Risparmio netto base [€/anno]
    param : str
        Parametro da variare: 'CAPEX_preheater', 'discount_rate', 
        'project_lifetime', 'OPEX_annual'
    values : list
        Lista di valori da testare

    Ritorna
    -------
    list di dict con {param_value, NPV}

    Esempio
    -------
    >>> sensitivity_analysis(50000, 'discount_rate', [0.05, 0.08, 0.10, 0.12])
    """
    results = []
    original = ECONOMICS[param]

    for v in values:
        ECONOMICS[param] = v
        npv = simple_npv(annual_net_saving)
        results.append({"param_value": v, "NPV_eur": npv})

    ECONOMICS[param] = original  # Ripristina valore originale
    return results
