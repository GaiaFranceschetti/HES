# =============================================================================
# analysis/plots.py — Grafici publication-ready per il paper
# =============================================================================
# Tutti i grafici usano uno stile coerente, adatto per pubblicazione.
# I file vengono salvati nella cartella results/
# =============================================================================

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import os

# --- Stile globale per il paper ----------------------------------------------
plt.rcParams.update({
    "font.family":       "serif",
    "font.size":         11,
    "axes.labelsize":    12,
    "axes.titlesize":    13,
    "legend.fontsize":   10,
    "figure.dpi":        150,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "lines.linewidth":   1.8,
})

COLORS = {
    "el_price":    "#E63946",   # rosso — prezzo elettricità
    "preheater":   "#2196F3",   # blu  — stato preheater
    "gas":         "#FF9800",   # arancio — gas
    "saving":      "#4CAF50",   # verde — risparmio netto
    "baseline":    "#9E9E9E",   # grigio — scenario senza preheater
}

RESULTS_DIR = "results/"
os.makedirs(RESULTS_DIR, exist_ok=True)


# =============================================================================
# FIGURA 1 — Curva di sizing stazionario
# =============================================================================

def plot_sizing_curve(sizing_results: list, save: bool = True):
    """
    Mostra come variano T_aria_out, Q_thermico e risparmio gas
    al variare della potenza elettrica installata.

    Da usare nel capitolo di sizing del paper.
    """
    P    = [r["P_el_kw"]           for r in sizing_results]
    T    = [r["T_air_out"]         for r in sizing_results]
    Q    = [r["Q_reale_kw"]        for r in sizing_results]
    dgas = [r["gas_savings_eur_h"] for r in sizing_results]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    fig.suptitle("Curva di sizing del preheater ad induzione", fontweight="bold")

    axes[0].plot(P, T, color=COLORS["preheater"])
    axes[0].set_xlabel("Potenza elettrica [kW]")
    axes[0].set_ylabel("T aria uscita [°C]")
    axes[0].set_title("Temperatura aria preriscaldata")

    axes[1].plot(P, Q, color=COLORS["gas"])
    axes[1].set_xlabel("Potenza elettrica [kW]")
    axes[1].set_ylabel("Calore trasferito [kW]")
    axes[1].set_title("Potenza termica effettiva")

    axes[2].plot(P, dgas, color=COLORS["saving"])
    axes[2].set_xlabel("Potenza elettrica [kW]")
    axes[2].set_ylabel("Risparmio gas [€/h]")
    axes[2].set_title("Risparmio economico (gas)")

    plt.tight_layout()
    if save:
        plt.savefig(RESULTS_DIR + "fig1_sizing_curve.png", bbox_inches="tight")
        print("  Salvato: fig1_sizing_curve.png")
    plt.show()


# =============================================================================
# FIGURA 2 — Due giorni a confronto (basso vs alto prezzo)
# =============================================================================

def plot_two_days(df: pd.DataFrame,
                  date_low: str,
                  date_high: str,
                  save: bool = True):
    """
    Confronta il comportamento del sistema in due giorni tipici:
    - un giorno con prezzi bassi (preheater prevalentemente ON)
    - un giorno con prezzi alti (preheater prevalentemente OFF)

    Parametri
    ---------
    df : DataFrame
        Output della simulazione annuale
    date_low : str
        Data giorno a basso prezzo (es. "2023-06-15")
    date_high : str
        Data giorno ad alto prezzo (es. "2023-01-20")

    Esempio chiamata
    ----------------
    plot_two_days(results, date_low="2023-06-15", date_high="2023-01-20")
    """
    def get_day(df, date):
        mask = df["timestamp"].dt.date == pd.to_datetime(date).date()
        return df[mask].copy()

    day_low  = get_day(df, date_low)
    day_high = get_day(df, date_high)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle("Confronto giorni: basso vs alto prezzo elettricità",
                 fontweight="bold", fontsize=14)

    for col_idx, (day, label, color) in enumerate([
        (day_low,  f"Basso prezzo ({date_low})",  "#1976D2"),
        (day_high, f"Alto prezzo ({date_high})",   "#D32F2F"),
    ]):
        hours = day["timestamp"].dt.hour

        # Riga superiore — Prezzo + stato preheater
        ax = axes[0][col_idx]
        ax2 = ax.twinx()
        ax.plot(hours, day["price_eur_mwh"], color=color, label="Prezzo el.")
        ax2.fill_between(hours, day["preheater_on"].astype(int),
                         alpha=0.2, color=COLORS["preheater"], label="Preheater ON")
        ax.set_title(label)
        ax.set_ylabel("Prezzo [€/MWh]")
        ax2.set_ylabel("Preheater ON/OFF")
        ax2.set_ylim(0, 1.5)
        ax.set_xlabel("Ora del giorno")

        # Riga inferiore — Risparmio netto
        ax = axes[1][col_idx]
        ax.bar(hours, day["net_saving_eur"],
               color=[COLORS["saving"] if v >= 0 else COLORS["el_price"]
                      for v in day["net_saving_eur"]],
               alpha=0.8)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_ylabel("Risparmio netto [€/h]")
        ax.set_xlabel("Ora del giorno")
        ax.set_title("Risparmio netto orario")

    # Terza colonna — Confronto diretto risparmio cumulato
    ax = axes[0][2]
    ax.plot(hours, day_low["net_saving_eur"].cumsum(),
            color="#1976D2", label=f"Basso prezzo ({date_low})")
    ax.plot(hours, day_high["net_saving_eur"].cumsum(),
            color="#D32F2F", label=f"Alto prezzo ({date_high})")
    ax.set_title("Risparmio cumulato giornaliero")
    ax.set_ylabel("Risparmio cumulato [€]")
    ax.set_xlabel("Ora del giorno")
    ax.legend()

    ax = axes[1][2]
    ax.plot(hours, day_low["price_eur_mwh"],
            color="#1976D2", label=f"Basso prezzo")
    ax.plot(hours, day_high["price_eur_mwh"],
            color="#D32F2F", label=f"Alto prezzo")
    ax.axhline(50, color="black", linestyle="--",
               linewidth=1, label="Soglia controllo")
    ax.set_title("Profilo prezzi a confronto")
    ax.set_ylabel("Prezzo [€/MWh]")
    ax.set_xlabel("Ora del giorno")
    ax.legend()

    plt.tight_layout()
    if save:
        plt.savefig(RESULTS_DIR + "fig2_two_days.png", bbox_inches="tight")
        print("  Salvato: fig2_two_days.png")
    plt.show()


# =============================================================================
# FIGURA 3 — Panoramica annuale
# =============================================================================

def plot_annual_overview(df: pd.DataFrame, save: bool = True):
    """
    Tre grafici per la panoramica annuale:
    - Prezzi medi mensili + frazione ore preheater ON
    - Risparmio netto mensile
    - Heatmap prezzo per ora del giorno × mese
    """
    monthly = df.groupby("month").agg(
        price_mean     = ("price_eur_mwh",  "mean"),
        fraction_on    = ("preheater_on",   "mean"),
        net_saving     = ("net_saving_eur", "sum"),
        el_cost        = ("el_cost_eur",    "sum"),
        gas_savings    = ("gas_savings_eur","sum"),
    ).reset_index()

    months = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
              "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Panoramica annuale del sistema", fontweight="bold")

    # --- Grafico 1: Prezzo medio + attivazione preheater ---
    ax1 = axes[0]
    ax2 = ax1.twinx()
    bars = ax1.bar(monthly["month"], monthly["price_mean"],
                   color=COLORS["el_price"], alpha=0.6, label="Prezzo medio el.")
    ax2.plot(monthly["month"], monthly["fraction_on"] * 100,
             color=COLORS["preheater"], marker="o", label="% ore ON")
    ax1.set_xlabel("Mese")
    ax1.set_ylabel("Prezzo medio [€/MWh]")
    ax2.set_ylabel("Ore preheater ON [%]")
    ax1.set_title("Prezzo elettricità e attivazione")
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(months, fontsize=9)

    # --- Grafico 2: Risparmio netto mensile ---
    ax = axes[1]
    bar_colors = [COLORS["saving"] if v >= 0 else COLORS["el_price"]
                  for v in monthly["net_saving"]]
    ax.bar(monthly["month"], monthly["net_saving"],
           color=bar_colors, alpha=0.8, label="Risparmio netto")
    ax.plot(monthly["month"], monthly["gas_savings"],
            color=COLORS["gas"], linestyle="--", marker="s",
            label="Risparmio gas (lordo)")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Mese")
    ax.set_ylabel("€/mese")
    ax.set_title("Risparmio netto mensile")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(months, fontsize=9)
    ax.legend()

    # --- Grafico 3: Heatmap prezzo orario ---
    ax = axes[2]
    pivot = df.pivot_table(values="price_eur_mwh",
                           index="hour", columns="month", aggfunc="mean")
    im = ax.imshow(pivot, aspect="auto", cmap="RdYlGn_r",
                   origin="lower", interpolation="nearest")
    plt.colorbar(im, ax=ax, label="Prezzo [€/MWh]")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Ora del giorno")
    ax.set_title("Heatmap prezzi: ora × mese")
    ax.set_xticks(range(12))
    ax.set_xticklabels(months, fontsize=8)
    ax.set_yticks(range(0, 24, 4))

    plt.tight_layout()
    if save:
        plt.savefig(RESULTS_DIR + "fig3_annual_overview.png", bbox_inches="tight")
        print("  Salvato: fig3_annual_overview.png")
    plt.show()


# =============================================================================
# FIGURA 4 — Transitorio dinamico (accensione/spegnimento)
# =============================================================================

def plot_dynamic_transient(time_min, Q_history, T_history, save: bool = True):
    """
    Mostra il transitorio di accensione e spegnimento del preheater.

    Parametri
    ---------
    time_min  : array [minuti]
    Q_history : array [kW] potenza termica nel tempo
    T_history : array [°C] temperatura aria uscita
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    fig.suptitle("Transitorio dinamico del preheater", fontweight="bold")

    ax1.plot(time_min, Q_history, color=COLORS["preheater"])
    ax1.set_ylabel("Potenza termica [kW]")
    ax1.set_title("Risposta del sistema all'accensione e spegnimento")

    ax2.plot(time_min, T_history, color=COLORS["gas"])
    ax2.set_ylabel("T aria uscita [°C]")
    ax2.set_xlabel("Tempo [min]")

    # Marcatori accensione/spegnimento
    t_mid = time_min[len(time_min)//2]
    for ax in [ax1, ax2]:
        ax.axvline(0,     color="green", linestyle="--",
                   alpha=0.7, label="Accensione")
        ax.axvline(t_mid, color="red",   linestyle="--",
                   alpha=0.7, label="Spegnimento")
        ax.legend(fontsize=9)

    plt.tight_layout()
    if save:
        plt.savefig(RESULTS_DIR + "fig4_transient.png", bbox_inches="tight")
        print("  Salvato: fig4_transient.png")
    plt.show()
