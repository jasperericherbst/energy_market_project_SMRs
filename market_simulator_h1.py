# -*- coding: utf-8 -*-
""" 
Created on Tue Feb  6 2023
@author: Carlos González de Miguel
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
        self.price   = []
        
        for x in data_range:
            self.power.append(data_OCCV['Potencia Compra/Venta'][x]) # MW
            self.price.append(data_OCCV['Precio Compra/Venta'][x]) # €/MW
        
        self.power_cumsum = np.round(np.cumsum(self.power),1) # Cumulative sum of power bids.
    
    def plot(self):
        plt.figure(figsize=(10, 6))
        plt.step(self.power_cumsum, self.price, 'green', linewidth=1, drawstyle='steps-pre', label=self.label)
        plt.title(self.label)
        plt.xlabel('Power [MW]')
        plt.ylabel('Price [€/MW]')
        plt.legend()
        plt.grid()
    
    def add_bid(self, price, power):
        self.price.append(price)
        if self.BuySell == 'V':
            self.price.sort(reverse=False)
        else:
            self.price.sort(reverse=True)
        self.power.insert(self.price.index(price), power)
        self.power_cumsum = np.round(np.cumsum(self.power),1) # Cumulative sum of power bids.

# Define the base class cross_curve (from a supply and demand curve)
class crossing_curves():
    def __init__(self, supply_curve, demand_curve):
        self.supply = supply_curve
        self.demand = demand_curve
    
    def plot(self):
        plt.figure(figsize=(8, 6))
        plt.step(self.demand.power_cumsum, self.demand.price, 'darkturquoise', linewidth=2, drawstyle='steps-pre', label=self.demand.label)
        plt.step(self.supply.power_cumsum, self.supply.price, 'green', linewidth=2, drawstyle='steps-pre', label=self.supply.label)
        plt.title('Supply and Demand curves - '+ str(self.demand.hour) + ' - ' + str(self.power_cleared) + 'MW; '+ str(self.price_buy) + 'EUR/MW')
        plt.xlabel('Power [MW]')
        plt.ylabel('Price [€/MW]')
        plt.legend()
        plt.grid()
    
    def clearing(self):
        power_cumsum_demand = np.round(np.cumsum(self.demand.power), 1)
        power_cumsum_supply = np.round(np.cumsum(self.supply.power), 1)
        
        matching_sell_prices = []
        cross = []
        
        # Returns the index of the supply bid with the same cumulative power as the demand bids.
        # Problem: searchsorted only works if the total cumulative demand power is smaller that the total cumulative supply power.
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

        true_indices = np.where(cross)[0]  # returns indices where values are True
        last_true_index = int(true_indices[-1])
        
        self.price_buy  = self.demand.price[last_true_index]
        self.price_sell = matching_sell_prices[last_true_index]
        self.power_cleared = power_cumsum_demand[last_true_index]
        
        print('Cleared power =', self.power_cleared, 'MW')
        print('Cleared price =', self.price_buy, '-', self.price_sell,'€/MW')
        
        return self.power_cleared, self.price_buy, self.price_sell


#============================ INPUT DATA ======================================
filename = 'curva_pbc_uof_20251001.1'
day = market_data(filename)
#filtered = day.bids[day.bids["Unidad"] == "ABO2G"]
filtered = day.bids[
    (day.bids["Unidad"] == "MIEU") | 
    (day.bids["Unidad"] == "MIP")
]
# Arrays to store info for plotting
# Arrays to store info for plotting
quarter_index_array = []
unidad_array = []
tipo_oferta_array = []

# Helper function: convert OMIE period to 1..96 quarter index
def period_to_index(p):
    h = int(p.split("Q")[0][1:])
    q = int(p.split("Q")[1])
    return (h-1)*4 + q

# Iterate filtered bids
for _, row in filtered.iterrows():
    ts = row["Periodo"]
    unidad = row["Unidad"]
    tipo_oferta = row["Tipo Oferta"]
    
    quarter_index_array.append(period_to_index(ts))
    unidad_array.append(unidad)
    tipo_oferta_array.append(tipo_oferta)
    
    country = (unidad=="MIEU")*"France" + (unidad=="MIP")*"Portugal"
    flow = (tipo_oferta=="C")*"Import" + (tipo_oferta=="V")*"Export"
    print(ts, unidad + " " + country, flow)

# Prepare x/y positions and markers
x_import_fr = [quarter_index_array[i] for i,u in enumerate(unidad_array) if u=="MIEU" and tipo_oferta_array[i]=="C"]
x_export_fr = [quarter_index_array[i] for i,u in enumerate(unidad_array) if u=="MIEU" and tipo_oferta_array[i]=="V"]
x_import_pt = [quarter_index_array[i] for i,u in enumerate(unidad_array) if u=="MIP" and tipo_oferta_array[i]=="C"]
x_export_pt = [quarter_index_array[i] for i,u in enumerate(unidad_array) if u=="MIP" and tipo_oferta_array[i]=="V"]

y_fr = 1
y_pt = 0

# Plot figure
plt.figure(figsize=(10,2))

# France
plt.scatter(x_import_fr, [y_fr]*len(x_import_fr), color="blue", marker='o', label="France Import")
plt.scatter(x_export_fr, [y_fr]*len(x_export_fr), color="blue", marker='x', label="France Export")

# Portugal
plt.scatter(x_import_pt, [y_pt]*len(x_import_pt), color="green", marker='o', label="Portugal Import")
plt.scatter(x_export_pt, [y_pt]*len(x_export_pt), color="green", marker='x', label="Portugal Export")

# x-axis: first quarter of each hour
hour_ticks = [(h-1)*4 + 1 for h in range(1,25)]
plt.xticks(hour_ticks, range(1,25))
plt.yticks([0,1], ["Portugal","France"])
plt.xlabel("Hour of day")
plt.title("Interconnection bids during the day")
plt.legend(loc="upper right", fontsize=8)
plt.grid(axis="x", linestyle="--", alpha=0.3)
plt.tight_layout()

#offered_supply.plot()
#offered_demand.plot()


# price_buy_array = []
# power_array = []
# hour_array = []
# difference_array = []


# H = 1
# while H<=24:
#     Q = 1
#     while Q<=4:
        
#         hour = 'H' + str(H) + 'Q' + str(Q)
#         hour_array.append(hour);
#         print(hour);
#         # Find more market results here: https://www.omie.es/en/file-access-list
        
#         #=========================== DO NOT EDIT ======================================
        
#         offered_supply = curve(day.bids, hour, 'O', 'V', 'Supply curve (offered bids)')
#         offered_demand = curve(day.bids, hour, 'O', 'C', 'Demand curve (offered bids)')
#         supply_demand  = crossing_curves(offered_supply, offered_demand)
        
#         #========================= OBTAIN RESULTS =====================================
#         #print('')
#         #print('MARKET BIDS (market solution): ')
#         #print('======================================================================')
#         #offered_supply.plot()
#         #offered_demand.plot()
#         power, price_buy, price_sell = supply_demand.clearing()
#         price_buy_array.append(price_buy)
#         power_array.append(power);
#         #supply_demand.plot()
        
        
#         offered_supply_c = curve(day.bids, hour, 'C', 'V', 'Supply curve (offered bids)')
#         offered_demand_c = curve(day.bids, hour, 'C', 'C', 'Demand curve (offered bids)')
#         supply_demand_c  = crossing_curves(offered_supply_c, offered_demand_c)
#         power_c, price_buy_c, price_sell_c = supply_demand_c.clearing()
        
#         difference = price_buy_c-price_buy
#         difference_array.append(difference)
        
#         Q = Q +1;
#     H = H +1;


# avg_dif = np.mean(difference_array)
# print(str(avg_dif)+" €/MW")

# plt.figure(figsize=(10,6))
# plt.plot(hour_array, difference_array, marker='o', label='Buy/Clear price difference')
# plt.title('Hourly cleared price difference')
# plt.xlabel('Hour')
# plt.ylabel('Price [€/MW]')
# plt.xticks(
#      ticks=range(0, len(hour_array), 4),
#      labels=hour_array[::4],
#      rotation=45
# )

# plt.axhline(y=avg_dif, linestyle='--', label='Daily average diff')



# avg_price = np.mean(price_buy_array)
# print(str(avg_price) + " €/MW")

# Plot the curve of buy-prices for the 24 h x 4 quarters. 

# plt.figure(figsize=(10,6))
# plt.plot(hour_array, price_buy_array, marker='o', label='Buy price')

# # --- average line ---
# plt.axhline(y=avg_price, linestyle='--', label='Daily average')

# plt.title('Hourly cleared buy price')
# plt.xlabel('Hour')
# plt.ylabel('Price [€/MW]')

# plt.xticks(
#     ticks=range(0, len(hour_array), 4),
#     labels=hour_array[::4],
#     rotation=45
# )

# plt.grid(True)
# plt.legend()
# plt.tight_layout()
# plt.show()
# # Plot the curve of cleared demand for the24 h x 4 quarters

# plt.figure(figsize=(10,6))
# plt.plot(hour_array, power_array, marker='o', c = 'green')
# plt.title('Hourly cleared demand')
# plt.xlabel('Hour')
# plt.ylabel('Demand [MWh]')
# plt.xticks(
#     ticks=range(0, len(hour_array), 4),
#     labels=hour_array[::4],
#     rotation=45
# )
# plt.grid(True)
# plt.tight_layout()
# plt.show()


#%%
# ============================== CANIBALIZATION ===============================
# print('')
# print('CANIBALIZATION OF RENEWABLES: ')
# print('======================================================================')
# canibalized_supply = curve(day.bids, hour, 'O', 'V', 'Canibalized supply curve (offered bids)')
# new_bid_power = 5000 # MWh
# new_bid_price  = 0 # €/MWh
# print('Added a supply bid of', new_bid_power, 'MW, at a price of', new_bid_price, 'EUR/MW')
# canibalized_supply.add_bid(new_bid_price, new_bid_power)
# canibalized_supply_demand  = crossing_curves(canibalized_supply, offered_demand)
# canibalized_power, canibalized_price_buy, canibalized_price_sell = canibalized_supply_demand.clearing()
# canibalized_supply_demand.plot()


#%%
# ============================== ELECTRIFICATION ==============================
# print('')
# print('ELECTRIFICATION OF THE ECONOMY: ')
# print('======================================================================')
# electrified_demand = curve(day.bids, hour, 'O', 'C', 'Electrified supply curve (offered bids)')
# new_bid_power = 5000 # MWh
# new_bid_price  = 1400 # €/MWh
# print('Added a demand bid of', new_bid_power, 'MW, at a price of', new_bid_price, '€/MW')
# electrified_demand.add_bid(new_bid_price, new_bid_power)
# electrified_supply_demand  = crossing_curves(offered_supply, electrified_demand)
# electrified_power, electrified_price_buy, electrified_price_sell = electrified_supply_demand.clearing()
# electrified_supply_demand.plot()
