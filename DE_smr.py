# -*- coding: utf-8 -*-
"""
Plotting German Electricity Market Prices, SMR Thresholds, and Profitability
"""

import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
# 1. SETUP SMR PARAMETERS
# =============================================================================
smr_types = {
    'SMR Type 1 (PWR)': 33.6,
    'SMR Type 2 (FR_LowerBound)': 76.67,
    'SMR Type 3 (FR_UpperBound)': 335.35
}

# Add the plant capacity in Megawatts (MW)
capacity_mw = 300 

# Define the exact column names from your CSV
file_name = 'Day-ahead_prices_202603150000_202603260000_Hour.csv' # <-- Replace with your actual file name!
col_start_date = 'Start date'
col_price = 'Germany/Luxembourg [€/MWh] Calculated resolutions'

# =============================================================================
# 2. LOAD AND CLEAN THE DATA
# =============================================================================
print("Loading data...")

df = pd.read_csv(file_name, sep=';', decimal='.') 

# Clean up any potential empty spaces in column names
df.columns = df.columns.str.strip()

# Convert the 'Start date' column to actual datetime objects
df[col_start_date] = pd.to_datetime(df[col_start_date], dayfirst=True, errors='coerce')

# Drop any rows where the date or price is missing
df = df.dropna(subset=[col_start_date, col_price])

# Sort the data chronologically
df = df.sort_values(by=col_start_date)

# =============================================================================
# 3. PLOT THE DATA
# =============================================================================
print("Generating plot...")
plt.figure(figsize=(14, 7))

# Plot the actual market price curve
plt.plot(df[col_start_date], df[col_price], color='steelblue', linewidth=1.5, label='Market Price (Germany/Luxembourg)')

# Plot the horizontal lines for the 3 SMR types
colors = ['green', 'orange', 'red']
for (smr_name, smr_price), color in zip(smr_types.items(), colors):
    plt.axhline(y=smr_price, color=color, linestyle='--', linewidth=2, label=f'{smr_name} ({smr_price} €/MWh)')

# Formatting the chart
plt.title('German Electricity Market Prices vs. SMR Bid Thresholds', fontsize=14, fontweight='bold')
plt.xlabel('Date / Time', fontsize=12)
plt.ylabel('Price [€/MWh]', fontsize=12)
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right', framealpha=0.9)
plt.xticks(rotation=45)
plt.tight_layout()

# Display the plot without freezing the script
plt.show(block=False) 

# =============================================================================
# 4. CALCULATE PROFITS AND STORE FILTERED DATA
# =============================================================================
print("\n==================================================")
print(f" FINANCIAL SUMMARY (Capacity: {capacity_mw} MW) ")
print("==================================================")

profitable_periods = {}
total_hours = len(df)

# Assuming total_hours is the length of your full dataframe
total_hours_period = len(df)

for smr_name, smr_price in smr_types.items():
    # 1. Revenue: Sum of ALL market prices in the dataset * Capacity
    # (Since it's always selling, we use the full 'df', not the filtered one)
    total_revenue = df[col_price].sum() * capacity_mw
    
    # 2. Cost: Fixed SMR price * EVERY hour in the period * Capacity
    total_cost = (smr_price * total_hours_period) * capacity_mw
    
    # 3. Profit: This could now be negative if market prices are low
    total_profit = total_revenue - total_cost
    
    # 4. Analysis of "Loss-Making" hours
    # Even though we sell, it's useful to know how often we sold below cost
    below_threshold = df[df[col_price] < smr_price]
    loss_hours = len(below_threshold)
    loss_percentage = (loss_hours / total_hours_period) * 100

    # Print the results
    print(f"\n--- {smr_name} (Always-On Operational Model) ---")
    print(f" Marginal Cost  : {smr_price} €/MWh")
    print(f" Total Hours    : {total_hours_period:,} hours")
    print(f" Hours @ Loss   : {loss_hours:,} hours ({loss_percentage:.1f}%)")
    print(f" ----------------------------------------------")
    print(f" Total Revenue  : €{total_revenue:,.2f}")
    print(f" Total Cost     : €{total_cost:,.2f}")
    print(f" Net Profit     : €{total_profit:,.2f}")

print("\n==================================================")

# Keep the plot window open
plt.show()