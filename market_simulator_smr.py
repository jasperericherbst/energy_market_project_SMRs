# -*- coding: utf-8 -*-
""" 
Created on Tue Feb  6 2023
@author: Carlos González de Miguel
Modified to highlight specific unit bids (SMR) and auto-sort manually added bids.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define the base class market_data
class market_data():
    def __init__(self, filename):
        self.filename = filename
        self.bids = pd.read_csv(self.filename, sep=';', decimal=',', thousands='.', encoding='latin1', skiprows=2, engine='python', skipfooter=1)

# Define the base class curve (obtained after splitting the market data)
class curve():
    def __init__(self, bids, hour, OfferedCleared, BuySell, label):
        self.hour           = hour
        self.OfferedCleared = OfferedCleared
        self.BuySell        = BuySell
        self.label          = label
        
        data_hour  = bids[bids['Periodo'] == self.hour]
        data_OC    = data_hour[data_hour['Ofertada (O)/Casada (C)'] == self.OfferedCleared]
        data_OCCV  = data_OC[data_OC['Tipo Oferta'] == self.BuySell] # Buy(C)/Sell(V)
        data_range = data_OC[data_OC['Tipo Oferta'] == self.BuySell].index.tolist()
        
        self.power  = []
        self.price  = []
        self.units  = [] # NEW: Storing unit names to identify SMR
        
        # Helper function to ensure safe conversion of OMIE numbers for sorting
        def safe_float(val):
            val_str = str(val).strip()
            if '.' in val_str and ',' in val_str:
                return float(val_str.replace('.', '').replace(',', '.'))
            elif ',' in val_str:
                return float(val_str.replace(',', '.'))
            return float(val_str)

        for x in data_range:
            self.power.append(safe_float(data_OCCV['Potencia Compra/Venta'][x])) 
            self.price.append(safe_float(data_OCCV['Precio Compra/Venta'][x])) 
            self.units.append(data_OCCV['Unidad'][x]) 
            
        # --- NEW: SORTING LOGIC ---
        # Zip the lists together so they stay perfectly aligned when sorting
        combined = list(zip(self.price, self.power, self.units))
        
        if self.BuySell == 'V':
            # Supply curve: Sort ascending (lowest price first)
            combined.sort(key=lambda x: x[0], reverse=False)
        else:
            # Demand curve: Sort descending (highest price first)
            combined.sort(key=lambda x: x[0], reverse=True)
            
        # Unzip the sorted tuples back into their separate lists
        self.price, self.power, self.units = map(list, zip(*combined))
        
        # Calculate cumulative sum AFTER sorting
        self.power_cumsum = np.round(np.cumsum(self.power),1) 
    
    def plot(self):
        plt.figure(figsize=(10, 6))
        plt.step(self.power_cumsum, self.price, 'green', linewidth=1, drawstyle='steps-pre', label=self.label)
        plt.title(self.label)
        plt.xlabel('Power [MW]')
        plt.ylabel('Price [€/MW]')
        plt.legend()
        plt.grid()
    
    def add_bid(self, price, power, unit_name='UNKNOWN'):
        self.price.append(price)
        if self.BuySell == 'V':
            self.price.sort(reverse=False)
        else:
            self.price.sort(reverse=True)
        insert_idx = self.price.index(price)
        self.power.insert(insert_idx, power)
        self.units.insert(insert_idx, unit_name) 
        self.power_cumsum = np.round(np.cumsum(self.power),1)

# Define the base class cross_curve (from a supply and demand curve)
class crossing_curves():
    def __init__(self, supply_curve, demand_curve):
        self.supply = supply_curve
        self.demand = demand_curve
    
    def plot(self, highlight_unit='SMR', not_included_unit='ISMRE05'):
        plt.figure(figsize=(10, 6))
        plt.step(self.demand.power_cumsum, self.demand.price, 'darkturquoise', linewidth=2, drawstyle='steps-pre', label=self.demand.label)
        plt.step(self.supply.power_cumsum, self.supply.price, 'green', linewidth=2, drawstyle='steps-pre', label=self.supply.label)
        
        # Highlight specific unit (SMR) with a dot
        for curve_obj in [self.supply, self.demand]:
            for i, unit in enumerate(curve_obj.units):
                if isinstance(unit, str) and highlight_unit in unit and not unit == not_included_unit:
                    # Place the dot in the middle of the bid's horizontal step
                    x_midpoint = curve_obj.power_cumsum[i] - (curve_obj.power[i] / 2)
                    y_val = curve_obj.price[i]
                    plt.plot(x_midpoint, y_val, 'ro', markersize=8, label=f'{unit} ({y_val} €/MW)')

        # Prevent duplicate labels in the legend if SMR has multiple bids
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())

        plt.title('Supply and Demand curves - '+ str(self.demand.hour) + ' - ' + str(self.power_cleared) + 'MW; '+ str(self.price_buy) + 'EUR/MW')
        plt.xlabel('Power [MW]')
        plt.ylabel('Price [€/MW]')
        plt.grid()
    
    def clearing(self):
        power_cumsum_demand = np.round(np.cumsum(self.demand.power), 1)
        power_cumsum_supply = np.round(np.cumsum(self.supply.power), 1)
        
        matching_sell_prices = []
        cross = []
        
        if (power_cumsum_demand[-1] > power_cumsum_supply[-1]):
            index_demand_max = np.searchsorted(power_cumsum_demand, power_cumsum_supply[-1], side='right')
            search_indexes = np.searchsorted(power_cumsum_supply, power_cumsum_demand[0:index_demand_max], side='left')
            for i in range(index_demand_max+1):
                matching_sell_prices.append(self.supply.price[search_indexes[i]])
                cross.append(self.demand.price[i] >= self.supply.price[search_indexes[i]])
        else:
            search_indexes = np.searchsorted(power_cumsum_supply, power_cumsum_demand, side='left')
            for i in range(len(search_indexes)):
                matching_sell_prices.append(self.supply.price[search_indexes[i]])
                cross.append(self.demand.price[i] >= self.supply.price[search_indexes[i]])

        true_indices = np.where(cross)[0] 
        last_true_index = int(true_indices[-1])
        
        self.price_buy  = self.demand.price[last_true_index]
        self.price_sell = matching_sell_prices[last_true_index]
        self.power_cleared = power_cumsum_demand[last_true_index]
        
        print('Cleared power =', self.power_cleared, 'MW')
        print('Cleared price =', self.price_buy, '-', self.price_sell,'€/MW')
        
        return self.power_cleared, self.price_buy, self.price_sell

#============================ INPUT DATA ======================================
filename = 'curva_pbc_uof_20251001_SMRs.1'

H = 21 # hour values from 1 to 24
Q = 1 # quarter values from 1 to 4

hour = 'H' + str(H) + 'Q' + str(Q)

day = market_data(filename)
offered_supply = curve(day.bids, hour, 'O', 'V', 'Supply curve (offered bids)')
offered_demand = curve(day.bids, hour, 'O', 'C', 'Demand curve (offered bids)')
supply_demand  = crossing_curves(offered_supply, offered_demand)

#========================= OBTAIN RESULTS =====================================
print('')
print('MARKET BIDS (market solution): ')
print('======================================================================')
power, price_buy, price_sell = supply_demand.clearing()
supply_demand.plot()
plt.show()