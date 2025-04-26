import random
import matplotlib.pyplot as plt
from itertools import product
from libs.graph import plot_gantt, plot_occupancy_rate, plot_inventory_graph
from libs.simulation import Simulator

# Configuration for simulation
SIM_TIME = 120
RANDOM_SEED = 42

# Store times
CHECK_STORE_TIME = 5 # 2800 minutes = Two days
DELIVERY_TIME = 100 # For shipment

# Probabilities
REQUEST_THRESHOLD = 50 # Expressed in %. Quantity of pieces in store to buy more parts
GOOD_PIECE_PROBABILITY = 90 # Probability for a new piece to not be discarded

PRIMARY_PARTS = ("front_fork", "tube", "damper", "sprokets",
                "pedals", "rear_fork", "saddle", "chain_rings", "front_rim",
                "rear_rim", "inner_tube", "derailleur", "right_control", "left_control",
                "brake", "cable", "chain", "tire")

random.seed(RANDOM_SEED)

simulation = Simulator(CHECK_STORE_TIME, DELIVERY_TIME, PRIMARY_PARTS, REQUEST_THRESHOLD, GOOD_PIECE_PROBABILITY, SIM_TIME)

possible_values = (1,2,3)

combinations = product(possible_values, repeat=10)
record_bikes = 0
for config in combinations:
    simulation.execute_simulation(config)
    total_bikes = simulation.count_produced_bikes()
    if total_bikes > record_bikes:
        record_bikes = total_bikes
        best_config = config
    elif (total_bikes == record_bikes) and ('record_bikes' in locals()):
        if sum(config) < sum(best_config):
            best_config = config

print(f'Best config: {best_config}')
simulation.execute_simulation(best_config)
plot_gantt(simulation.process_log, simulation.cable_assembler, SIM_TIME)
plot_occupancy_rate(simulation.process_log, SIM_TIME)
plot_inventory_graph(simulation.stock_log)
plt.show()