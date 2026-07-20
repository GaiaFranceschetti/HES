# =============================================================================
# config.py — Parametri del sistema
# =============================================================================
# Questo file contiene TUTTI i parametri fisici ed economici del modello.
# Quando selezioni la fornace, modifica solo questo file — il resto del codice
# non cambia.
# =============================================================================

# --- ARIA COMBURENTE ---------------------------------------------------------
AIR = {
    "T_in":       175.0,    # [°C]    Temperatura aria in ingresso (ambiente)
    "cp":         1005.0,  # [J/kgK] Calore specifico aria (costante, approx.)
    "rho":         1.2,    # [kg/m3] Densità aria a T ambiente
}

# --- PREHEATER AD INDUZIONE --------------------------------------------------
PREHEATER = {
    "eta_ind":     0.92,   # [-]     Efficienza elettrica→termica bobina induzione
    "effectiveness": 0.80, # [-]     ε scambiatore suscettore→aria  ← DA CALIBRARE
    "P_el_max":   200.0,   # [kW]   Potenza elettrica massima installata  ← DA SIZING
    "tau_min":      5.0,   # [min]  Costante di tempo termica (rampa accensione)
    "T_air_out_max": 500.0,# [°C]   Limite fisico temperatura aria uscita
    "delta_T_target": 200.0,  # [°C] target temperature rise in preheater
    "T_air_out_target": 375.0, # [°C] target air outlet temperature
}


# --- FORNACE (BLACK BOX) -----------------------------------------------------
FURNACE = {
    "Q_thermal":  1500.0,  # [kW]   Potenza termica totale fornace  ← DA SCHEDA TECNICA
    "eta_furnace": 0.75,   # [-]    Efficienza termica fornace
    "T_billet_target": 1200.0, # [°C] Temperatura target billette acciaio
    "throughput":   5.0,   # [ton/h] Produzione billette
    "operating_hours": 8000, # [h/anno] Ore operative annue
}

# --- GAS NATURALE ------------------------------------------------------------
GAS = {
    "LHV":        50.0,    # [MJ/kg] Lower Heating Value gas naturale
    "price":      0.04174,    # [€/kWh] Prezzo gas naturale  
    "density":    0.72,    # [kg/Nm3] Densità gas naturale
    "CO2_factor": 0.202,   # [kgCO2/kWh] Fattore emissioni gas naturale
}

# --- ECONOMIA ----------------------------------------------------------------
ECONOMICS = {
    "CAPEX_preheater": 150_000,  # [€]  Costo investimento preheater  ← DA PREVENTIVO
    "OPEX_annual":       5_000,  # [€/anno] Costi O&M annui stimati
    "discount_rate":      0.08,  # [-]  Tasso di sconto (8%)
    "project_lifetime":    15,   # [anni] Vita utile impianto
    "el_price_threshold": 36.8,  # [€/MWh] Soglia prezzo: sotto → preheater ON
}

# --- CONTROLLO ---------------------------------------------------------------
CONTROL = {
    "strategy": "threshold",  # "threshold" oppure "optimization"
    # threshold: accendi se prezzo < el_price_threshold
    # optimization: minimizza costo totale ogni ora (più avanzato)
}
