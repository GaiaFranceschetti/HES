# Induction Preheater — Energy Flexibility Model
### Industrial Energy Flexibility | University of Padova

---

## Project structure

```
induction_preheater/
│
├── main.py               ← Run this to execute everything
├── config.py             ← ALL physical & economic parameters (edit here)
├── economics.py          ← NPV, payback period, sensitivity analysis
│
├── models/
│   ├── preheater.py      ← Preheater model (steady-state + dynamic)
│   └── simulation.py     ← Annual simulation + dispatch controller
│
├── analysis/
│   └── plots.py          ← All paper figures (matplotlib)
│
├── data/
│   └── nordpool_2023.csv ← Put your Nord Pool price data here
│
└── results/              ← Output figures saved here automatically
    ├── fig1_sizing_curve.png
    ├── fig2_two_days.png
    ├── fig3_annual_overview.png
    └── fig4_transient.png
```

---

## How to run

### 1. Install dependencies
```bash
pip install numpy pandas matplotlib scipy
```

### 2. Add your Nord Pool data
Place your CSV file in `data/nordpool_2023.csv` with columns:
```
timestamp,price_eur_mwh
2023-01-01 00:00:00,45.2
2023-01-01 01:00:00,38.7
...
```
Nord Pool data can be downloaded from: https://www.nordpoolgroup.com/en/Market-data1/

### 3. Set your furnace parameters
Open `config.py` and fill in the values marked with `← DA SCHEDA TECNICA`:
- `FURNACE["Q_thermal"]`     — furnace thermal power [kW]
- `FURNACE["throughput"]`    — billet production rate [ton/h]
- `AIR["m_dot"]`             — combustion air mass flow [kg/s]
- `PREHEATER["P_el_max"]`    — installed electrical power [kW]
- `ECONOMICS["CAPEX_preheater"]` — investment cost [€]

### 4. Run the model
```bash
python main.py
```

---

## Model description

### Layer 1 — Steady-state sizing
Computes the preheater operating point for a given electrical input.
Key equations:
- `Q_ind = η_ind · P_el`                              (induction efficiency)
- `Q_max = ṁ_air · cp · (T_susceptor - T_air_in)`    (max transferable heat)
- `Q_real = min(Q_ind, ε · Q_max)`                    (ε-NTU method)
- `T_air_out = T_air_in + Q_real / (ṁ_air · cp)`     (outlet temperature)
- `Δṁ_gas = Q_real / (LHV · η_furnace)`              (gas savings)

### Layer 2 — Dynamic simulation
Simulates 8760 hourly time steps using Nord Pool spot prices.
Control logic: preheater ON if `price < threshold`, OFF otherwise.
Thermal ramp modelled as 1st-order lag: `τ · dQ/dt = Q_target - Q_current`

### Layer 3 — Economic analysis
- Annual net saving = gas savings - electricity cost
- NPV over project lifetime with discount rate
- Simple payback period
- Sensitivity analysis on key parameters

---

## Paper figures produced
| Figure | Content |
|--------|---------|
| fig1   | Sizing curve: T_air_out, Q_thermal, gas savings vs P_el |
| fig2   | Two-day comparison: low-price vs high-price day |
| fig3   | Annual overview: monthly savings + price heatmap |
| fig4   | Dynamic transient: ON→OFF thermal ramp |
