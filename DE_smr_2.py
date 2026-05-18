# -*- coding: utf-8 -*-
"""
Plotting German Electricity Market Prices, SMR Thresholds, and Profitability
Separated into Scenario 1 (Always-On) and Scenario 2 (Load-Following).
Processes multiple seasons automatically.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# =============================================================================
# 1. SETUP SMR PARAMETERS
# =============================================================================
smr_types = {
    'SMR Type 1 (PWR)': 33.6,
    'SMR Type 2 (FR_LowerBound)': 76.67,
    'SMR Type 3 (FR_UpperBound)': 335.35
}

# Plant capacity in Megawatts (MW)
capacity_mw = 300

# List of seasons to process
seasons = ['Spring', 'Summer', 'Fall', 'Winter']
folder_path = 'MarketData'

# Colors for the different SMR types
colors = ['green', 'orange', 'red']

# =============================================================================
# 2. LOOP THROUGH SEASONS, LOAD DATA, AND SIMULATE
# =============================================================================
for season in seasons:
    file_path = os.path.join(folder_path, f"{season}.csv")
    
    print(f"\n{'='*70}")
    print(f" PROCESSING SEASON: {season.upper()} ")
    print(f"{'='*70}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Skipping to next season...")
        continue
        
    print(f"Loading data from {file_path}...\n")
    
    # Read the CSV. SMARD German data uses commas for decimals
    df = pd.read_csv(file_path, sep=';', decimal=',')
    df.columns = df.columns.str.strip()
    
    # Dynamically grab columns (0: Start Date, 2: Price)
    col_start_date = df.columns[0] 
    col_price = df.columns[2]
    
    df[col_start_date] = pd.to_datetime(df[col_start_date], format='%d.%m.%Y %H:%M', errors='coerce')
    df = df.dropna(subset=[col_start_date, col_price])
    df = df.sort_values(by=col_start_date).reset_index(drop=True)
    
    total_hours = len(df)
    
    if total_hours == 0:
        print(f"No valid data found for {season}. Skipping...")
        continue

    # =============================================================================
    # SCENARIO 1: ALWAYS-ON (Reactor never turns off)
    # =============================================================================
    print(f"--- SCENARIO 1: ALWAYS-ON | {season.upper()} ---")
    
    # 1A. Calculate Financials for Scenario 1
    for smr_name, smr_price in smr_types.items():
        # Revenue is collected for every hour at the market price
        total_revenue_s1 = df[col_price].sum() * capacity_mw
        # Variable costs are incurred for every hour
        total_variable_cost_s1 = smr_price * capacity_mw * total_hours
        net_profit_s1 = total_revenue_s1 - total_variable_cost_s1
        
        # Calculate loss frequency (hours where market price < marginal cost)
        hours_at_loss = len(df[df[col_price] < smr_price])
        loss_frequency = (hours_at_loss / total_hours) * 100

        print(f"{smr_name} (MC: {smr_price} €/MWh)")
        print(f"  Total Revenue : €{total_revenue_s1:>15,.2f}")
        print(f"  Variable Cost : €{total_variable_cost_s1:>15,.2f}")
        print(f"  Net Profit    : €{net_profit_s1:>15,.2f}")
        print(f"  Loss Frequency: {loss_frequency:.1f}% ({hours_at_loss} hours)")
        print("-" * 40)

    # 1B. Plotting for Scenario 1 (Single combined graph)
    fig1, ax1 = plt.subplots(figsize=(14, 6))
    ax1.plot(df[col_start_date], df[col_price], color='steelblue', linewidth=1.5, label=f'Market Price ({season})')
    
    for (smr_name, smr_price), color in zip(smr_types.items(), colors):
        ax1.axhline(y=smr_price, color=color, linestyle='--', linewidth=2, label=f'{smr_name} ({smr_price} €/MWh)')

    ax1.set_title(f'Scenario 1: Always-On - Market Prices vs. Thresholds ({season})', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price [€/MWh]', fontsize=11)
    ax1.set_xlabel('Date / Time', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=9)
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig1.canvas.manager.set_window_title(f'Scenario 1 - {season}')
    plt.show(block=False)


    # =============================================================================
    # SCENARIO 2: LOAD-FOLLOWING (Reactor turns off when price < threshold)
    # =============================================================================
    print(f"\n--- SCENARIO 2: LOAD-FOLLOWING | {season.upper()} ---")
    
    # 2A. Setup Plotting for Scenario 2 (3 separated subplots)
    fig2, axes2 = plt.subplots(len(smr_types), 1, figsize=(14, 5 * len(smr_types)), sharex=True)
    if len(smr_types) == 1: axes2 = [axes2] # Handle case if only 1 SMR type is used

    # 2B. Calculate Financials & Plot Subplots for Scenario 2
    for idx, ((smr_name, smr_price), color) in enumerate(zip(smr_types.items(), colors)):
        ax = axes2[idx]
        
        # Boolean mask: True if market price > SMR marginal cost
        reactor_on = df[col_price] > smr_price
        df_on = df[reactor_on]
        
        hours_on = len(df_on)
        hours_off = total_hours - hours_on
        pct_on = (hours_on / total_hours) * 100

        # Financials: Only calculate revenue and costs for hours the reactor is ON
        total_revenue_s2 = df_on[col_price].sum() * capacity_mw
        total_variable_cost_s2 = smr_price * capacity_mw * hours_on
        net_profit_s2 = total_revenue_s2 - total_variable_cost_s2

        print(f"{smr_name} (MC: {smr_price} €/MWh)")
        print(f"  Hours ON      : {hours_on:>5} h ({pct_on:.1f}%)")
        print(f"  Hours OFF     : {hours_off:>5} h ({100 - pct_on:.1f}%)")
        print(f"  Total Revenue : €{total_revenue_s2:>15,.2f}")
        print(f"  Variable Cost : €{total_variable_cost_s2:>15,.2f}")
        print(f"  Net Profit    : €{net_profit_s2:>15,.2f}")
        print("-" * 40)

        # Plotting the separated graphs
        ax.plot(df[col_start_date], df[col_price], color='steelblue', linewidth=1, alpha=0.5, label='Market Price')

        # Shade ON periods (Green area OVER the threshold line)
        ax.fill_between(df[col_start_date], smr_price, df[col_price],
                        where=reactor_on, alpha=0.35, color='green', label='Selling (Profit Area)')

        # Shade OFF periods (Red area UNDER the threshold line)
        ax.fill_between(df[col_start_date], smr_price, df[col_price],
                        where=~reactor_on, alpha=0.15, color='red', label='Idle Gap (Avoided Loss)')

        # Effective selling line
        effective_price = df[col_price].where(reactor_on, other=smr_price)
        ax.plot(df[col_start_date], effective_price, color=color, linewidth=1.5)

        # Threshold line
        ax.axhline(y=smr_price, color='black', linestyle='--', linewidth=1.5, label=f'Threshold: {smr_price} €/MWh')

        ax.set_title(f'Scenario 2: {smr_name} - Load Following ({season})', fontsize=12, fontweight='bold')
        ax.set_ylabel('Price [€/MWh]', fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.7)
        ax.legend(loc='upper right', framealpha=0.9, fontsize=9)

    axes2[-1].set_xlabel('Date / Time', fontsize=11)
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig2.canvas.manager.set_window_title(f'Scenario 2 - {season}')
    plt.show(block=False)

print("\n==================================================")
print("All seasons processed. Check the generated plots.")
print("==================================================")

# Keep all plot windows open at the end
plt.show()