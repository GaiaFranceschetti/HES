# =============================================================================
# models/simulation.py — Simulazione annuale con dati prezzi reali
# =============================================================================
# Questo modulo:
#   1. Carica i prezzi elettricità (GEM, formato CSV)
#   2. Applica la logica di controllo ora per ora
#   3. Restituisce un DataFrame con tutti i risultati annuali
# =============================================================================

import numpy as np
import pandas as pd
from config import PREHEATER, ECONOMICS, FURNACE, GAS
from models.preheater import PreheaterSteadyState


# =============================================================================
# CONTROLLER — Logica di accensione/spegnimento
# =============================================================================

class ThresholdController:
    """
    Strategia di controllo semplice: accendi il preheater se il 
    prezzo dell'elettricità è sotto una soglia fissa.

    Questa è la baseline — semplice da implementare e da spiegare nel paper.
    """

    def __init__(self, threshold_eur_mwh: float = None):
        self.threshold = threshold_eur_mwh or ECONOMICS["el_price_threshold"]

    def decide(self, el_price: float) -> bool:
        """
        Ritorna True (preheater ON) se il prezzo è sotto soglia.

        Parametri
        ---------
        el_price : float
            Prezzo elettricità spot [€/MWh]
        """
        return el_price < self.threshold


# =============================================================================
# SIMULAZIONE ANNUALE
# =============================================================================

class AnnualSimulation:
    """
    Simula il sistema per un anno intero (8760 ore).

    Input:  DataFrame con prezzi orari elettricità
    Output: DataFrame con tutti i risultati ora per ora
    """

    def __init__(self, controller=None):
        self.preheater = PreheaterSteadyState()
        self.controller = controller or ThresholdController()
        self.P_el_max = PREHEATER["P_el_max"]

    def load_prices(self, filepath: str) -> pd.DataFrame:
        """
        Carica prezzi GEM da file CSV.

        Il file deve avere almeno due colonne:
            - 'timestamp' : data e ora (formato ISO: 2023-01-01 00:00:00)
            - 'price_eur_mwh' : prezzo spot [€/MWh]

        Parametri
        ---------
        filepath : str
            Percorso al file CSV con i prezzi

        Ritorna
        -------
        DataFrame con colonne: timestamp, price_eur_mwh
        """
        df = pd.read_csv(filepath, parse_dates=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Verifica che ci siano almeno 8760 ore
        if len(df) < 8760:
            print(f"  ATTENZIONE: il file ha solo {len(df)} ore (attese 8760)")

        print(f"  Prezzi caricati: {len(df)} ore")
        print(f"  Range date: {df['timestamp'].min()} → {df['timestamp'].max()}")
        print(f"  Prezzo medio: {df['price_eur_mwh'].mean():.1f} €/MWh")
        print(f"  Prezzo min:   {df['price_eur_mwh'].min():.1f} €/MWh")
        print(f"  Prezzo max:   {df['price_eur_mwh'].max():.1f} €/MWh")

        return df

    
    def run(self, prices_df: pd.DataFrame) -> pd.DataFrame:
        """
        Esegue la simulazione annuale ora per ora.

        Parametri
        ---------
        prices_df : DataFrame
            DataFrame con colonne: timestamp, price_eur_mwh

        Ritorna
        -------
        DataFrame con tutti i risultati orari
        """
        results = []

        for _, row in prices_df.iterrows():
            price = row["price_eur_mwh"]
            timestamp = row["timestamp"]

            # Controller decide se accendere il preheater
            preheater_on = self.controller.decide(price)
            P_el = self.P_el_max if preheater_on else 0.0

            # Calcola stato stazionario del preheater
            if preheater_on:
                state = self.preheater.run(P_el)
                T_air_out        = state["T_air_out"]
                Q_reale_kw       = state["Q_reale_kw"]
                delta_mgas_kgh   = state["delta_mgas_kgh"]
                gas_savings_eur  = state["gas_savings_eur_h"]
            else:
                T_air_out        = AIR_T_IN  = 20.0
                Q_reale_kw       = 0.0
                delta_mgas_kgh   = 0.0
                gas_savings_eur  = 0.0

            # Costo elettricità consumata [€/h]
            el_cost_eur = P_el * price / 1000  # kW * €/MWh / 1000 = €/h

            # Risparmio netto orario = risparmio gas - costo elettricità
            net_saving_eur = gas_savings_eur - el_cost_eur

            results.append({
                "timestamp":        timestamp,
                "price_eur_mwh":    price,
                "preheater_on":     preheater_on,
                "P_el_kw":          P_el,
                "T_air_out_C":      T_air_out,
                "Q_thermal_kw":     Q_reale_kw,
                "delta_mgas_kgh":   delta_mgas_kgh,
                "el_cost_eur":      el_cost_eur,
                "gas_savings_eur":  gas_savings_eur,
                "net_saving_eur":   net_saving_eur,
            })

        df_results = pd.DataFrame(results)

        # Aggiungi colonne temporali utili per i grafici
        df_results["month"]    = df_results["timestamp"].dt.month
        df_results["hour"]     = df_results["timestamp"].dt.hour
        df_results["weekday"]  = df_results["timestamp"].dt.dayofweek

        return df_results

    def summary(self, df_results: pd.DataFrame) -> dict:
        """
        Calcola i KPI annuali dalla simulazione.

        Parametri
        ---------
        df_results : DataFrame
            Output di run()

        Ritorna
        -------
        dict con tutti i KPI principali
        """
        hours_on = df_results["preheater_on"].sum()
        hours_tot = len(df_results)

        total_el_kwh       = df_results["P_el_kw"].sum()           # kWh/anno
        total_gas_saved    = df_results["delta_mgas_kgh"].sum()    # kg/anno
        total_el_cost      = df_results["el_cost_eur"].sum()       # €/anno
        total_gas_savings  = df_results["gas_savings_eur"].sum()   # €/anno
        total_net_saving   = df_results["net_saving_eur"].sum()    # €/anno

        # NPV semplificato
        from economics import simple_npv
        npv = simple_npv(total_net_saving)

        return {
            "ore_preheater_on":        hours_on,
            "frazione_on":             hours_on / hours_tot,
            "energia_elettrica_MWh":   total_el_kwh / 1000,
            "gas_risparmiato_ton":     total_gas_saved / 1000,
            "costo_elettricita_eur":   total_el_cost,
            "risparmio_gas_eur":       total_gas_savings,
            "risparmio_netto_eur":     total_net_saving,
            "npv_eur":                 npv,
        }
