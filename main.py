# =============================================================================
# main.py — Entry point: runs the full simulation pipeline
# =============================================================================
# Run this file to execute the complete analysis:
#   1. Steady-state sizing
#   2. Annual dynamic simulation
#   3. Economic analysis
#   4. Paper-ready plots
#
# Usage:
#   python main.py
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from config import PREHEATER, ECONOMICS

from models.preheater import PreheaterSteadyState, PreheaterDynamic
from models.simulation import AnnualSimulation, ThresholdController
from economics import lcoe_savings, sensitivity_analysis
from analysis.plots import (
    plot_sizing_curve,
    plot_two_days,
    plot_annual_overview,
    plot_dynamic_transient,
)


def run_sizing():
    """
    LAYER 1 — Steady-state sizing.
    Computes preheater performance across a range of electrical powers.
    """
    print("\n" + "="*60)
    print("  LAYER 1 — STEADY-STATE SIZING")
    print("="*60)

    ph = PreheaterSteadyState()

    # Single operating point (nominal)
    nominal = ph.run(PREHEATER["P_el_max"])
    print(f"\n  Nominal operating point (P_el = {PREHEATER['P_el_max']} kW):")
    for k, v in nominal.items():
        print(f"    {k:<25} {v:.2f}")

    # Full sizing curve
    sizing_results = ph.sizing_curve()
    plot_sizing_curve(sizing_results)

    return nominal, sizing_results


def run_dynamic_transient():
    """
    LAYER 2a — Dynamic transient.
    Simulates a single ON→OFF cycle to show the thermal ramp.
    """
    print("\n" + "="*60)
    print("  LAYER 2a — DYNAMIC TRANSIENT (ON → OFF cycle)")
    print("="*60)

    ph_dyn = PreheaterDynamic(dt_min=1.0)

    # Simulate 60 min ON, then 60 min OFF
    n_steps = 120
    time_min   = np.arange(n_steps)
    Q_history  = np.zeros(n_steps)
    T_history  = np.zeros(n_steps)

    for i in range(n_steps):
        # Switch OFF at t = 60 min
        P_target = PREHEATER["P_el_max"] if i < 60 else 0.0
        state = ph_dyn.step(P_target)
        Q_history[i] = state["Q_current_kw"]
        T_history[i] = state["T_air_out"]

    print(f"  Time constant τ = {PREHEATER['tau_min']} min")
    print(f"  Peak thermal power: {Q_history.max():.1f} kW")
    print(f"  Peak air temperature: {T_history.max():.1f} °C")

    plot_dynamic_transient(time_min, Q_history, T_history)

    return time_min, Q_history, T_history


def run_annual_simulation():
    """
    LAYER 2b — Annual simulation with real/synthetic electricity prices.
    """
    print("\n" + "="*60)
    print("  LAYER 2b — ANNUAL SIMULATION")
    print("="*60)

    sim = AnnualSimulation(
        controller=ThresholdController(
            threshold_eur_mwh=ECONOMICS["el_price_threshold"]
        )
    )

    # -------------------------------------------------------------------------
    
    # Option A: uncomment when you have the CSV file
    prices_df = sim.load_prices("{models,analysis,data,results}/Hourly_electricity_price.csv")


    print(f"\n  Control strategy: threshold at {ECONOMICS['el_price_threshold']} €/MWh")
    print(f"  Running hourly simulation for {len(prices_df)} hours...")

    results_df = sim.run(prices_df)

    print(f"\n  Simulation complete.")
    print(f"  Hours preheater ON:  {results_df['preheater_on'].sum()} h")
    print(f"  Hours preheater OFF: {(~results_df['preheater_on']).sum()} h")

    return results_df


def run_economics(results_df):
    """
    LAYER 3 — Economic analysis: NPV, payback, sensitivity.
    """
    print("\n" + "="*60)
    print("  LAYER 3 — ECONOMIC ANALYSIS")
    print("="*60)

    annual_net_saving = results_df["net_saving_eur"].sum()

    kpi = lcoe_savings(annual_net_saving)

    print(f"\n  Annual net saving:   {annual_net_saving:>10,.0f} €/year")
    print(f"  NPV:                 {kpi['NPV_eur']:>10,.0f} €")
    print(f"  Simple payback:      {kpi['payback_anni']:>10.1f} years")
    print(f"  Investment viable:   {'YES ✓' if kpi['redditivo'] else 'NO ✗'}")

    # Sensitivity: how does NPV change with electricity price threshold?
    print("\n  Sensitivity — control threshold vs NPV:")
    sens = sensitivity_analysis(
        annual_net_saving,
        param="el_price_threshold",
        values=[30, 40, 50, 60, 70, 80, 100]
    )
    # Note: sensitivity_analysis varies ECONOMICS params, not the simulation
    # For a full sensitivity, re-run the simulation for each value
    # This is a simplified version using the same annual_net_saving base

    return kpi


def run_plots(results_df):
    """
    Generate all paper figures.
    """
    print("\n" + "="*60)
    print("  GENERATING PAPER FIGURES")
    print("="*60)

    # Find a low-price day and a high-price day automatically
    daily_avg = results_df.groupby(results_df["timestamp"].dt.date)["price_eur_mwh"].mean()
    date_low  = str(daily_avg.idxmin())   # Day with lowest average price
    date_high = str(daily_avg.idxmax())   # Day with highest average price

    print(f"\n  Selected days for comparison:")
    print(f"    Low-price day:  {date_low}  (avg {daily_avg.min():.1f} €/MWh)")
    print(f"    High-price day: {date_high} (avg {daily_avg.max():.1f} €/MWh)")

    plot_two_days(results_df, date_low=date_low, date_high=date_high)
    plot_annual_overview(results_df)

    print("\n  All figures saved to results/")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    print("\n" + "="*60)
    print("  INDUCTION PREHEATER — ENERGY FLEXIBILITY MODEL")
    print("  Industrial Energy Flexibility — University of Padova")
    print("="*60)

    # Run all layers in sequence
    nominal, sizing_results = run_sizing()
    time_min, Q_hist, T_hist = run_dynamic_transient()
    results_df = run_annual_simulation()
    kpi = run_economics(results_df)
    run_plots(results_df)

    print("\n" + "="*60)
    print("  DONE. Check the results/ folder for all figures.")
    print("="*60 + "\n")
