import random
import simpy
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product

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

class Storage:
    def __init__(self, env):
        self.env = env
        self.inventory = {}
        for part in PRIMARY_PARTS:
            self.inventory[part] = simpy.Container(env, init=100, capacity=100)

    def check_level_low(self):
        for part in PRIMARY_PARTS:
            if self.inventory[part].level < self.inventory[part].capacity * REQUEST_THRESHOLD/100:
                return True 
        return False


    def get_good_pieces(self, new_pieces):
        good_pieces = 0
        for i in range(new_pieces):
            if random.randint(1,100) <= GOOD_PIECE_PROBABILITY:
                good_pieces += 1
        return good_pieces


    def fill(self):
        #print(f'{env.now} pieces arrived to store')
        for part in PRIMARY_PARTS:
            new_pieces = self.inventory[part].capacity - self.inventory[part].level
            good_pieces = self.get_good_pieces(new_pieces)
            if good_pieces>0: yield self.inventory[part].put(good_pieces)
            #print(f'{part} pieces: {self.inventory[part].level}')
        #print('')


    def request_shipment(self):
        while True:
            yield self.env.timeout(CHECK_STORE_TIME)
            if self.check_level_low():
                start_time = self.env.now
                #print(f'{start_time:.2f} Store under level, requesting pieces')
                yield self.env.timeout(DELIVERY_TIME)
                end_time = self.env.now
                process_log.append({'process_id': "Request shipment",
                                   'start': start_time,
                                   'end': end_time})
                yield self.env.process(self.fill())

def stock_monitor(env, store):
    interval = SIM_TIME / 20
    global stock_log
    stock_log = {"time": []}
    for part in store.inventory:
        stock_log[part] = []
    
    while True:
        stock_log["time"].append(env.now)
        for part in store.inventory:
            stock_log[part].append(store.inventory[part].level)

        yield env.timeout(interval)

def plot_inventory_graph():
    global stock_log
    max_curves = 10

    plt.figure(figsize=(12, 8))
    count = 0
    for item in stock_log:
        if count >= max_curves: break
        if item == 'time': continue
        plt.plot(stock_log['time'], stock_log[item], label=item.replace('_',' '))
        count += 1

    plt.title("Inventory levels")
    plt.xlabel("Time (min)")
    plt.ylabel("Quantity")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()


class Process_type:
    def __init__(self, env, store, times, name, input_stores, processes_quantity):
        self.env = env
        self.store = store
        self.times = times
        self.input_stores = input_stores
        self.out_container = simpy.Container(env, init=0)

        for i in range(processes_quantity):
            env.process(self.process(name + ' ' + str(i+1)))


    def process(self, id_process):
        while True:
            time = random.uniform(*self.times)
            for input in self.input_stores:
                if type(input) == Process_type:
                    yield input.out_container.get(1)
                else:
                    yield self.store.inventory[input].get(1)
            
            start_time = self.env.now
            #print(f'{start_time:.2f} {id_process} obtained parts and starts.')
            yield self.env.timeout(time)
            end_time = self.env.now
            yield self.out_container.put(1)
            #print(f'{end_time:.2f} {id_process} finished. Output store: {self.out_container.level}')

            process_log.append({'process_id': id_process,
                                'start': start_time,
                                'end': end_time})

def plot_occupancy_rate():
    global process_log
    sns.set_theme(style='ticks', context='talk')
    unique_processes = list(set(item['process_id'] for item in process_log))
    palette = sns.color_palette('Set3', n_colors=len(unique_processes))
    color_dict = {process: palette[i] for i, process in enumerate(unique_processes)}

    durations = {}
    for unique_process in unique_processes:
        durations[unique_process] = 0
    
    for item in process_log:
        durations[item['process_id']] += item["end"] - item["start"]

    fig, ax = plt.subplots(figsize=(12, 6))
    for process in durations:
        if process == 'Request shipment': continue
        relative_duration =  durations[process] *100/SIM_TIME
        ax.bar(x=process.replace(' ','\n'), height=relative_duration, color=color_dict[process], edgecolor='black')
        ax.set_ylabel('Active time (%)')

    ax.set_title('Occupancy rate')
    ax.grid(axis='y')
    ax.set_ylim((0,100))
    plt.tight_layout()

def plot_gantt():
    global process_log
    sns.set_theme(style='ticks', context='talk')

    unique_processes = list(set(item['process_id'] for item in process_log))
    palette = sns.color_palette('Set3', n_colors=len(unique_processes))
    color_dict = {process: palette[i] for i, process in enumerate(unique_processes)}

    fig, ax = plt.subplots(figsize=(12, 6))
    for item in process_log:
        process = item['process_id']
        start = item['start']
        finish = item['end']
        duration = finish - start
        #ax.axvline(x=start, color='gray', linewidth=0.8, alpha=0.5)
        #ax.axvline(x=finish, color='gray', linewidth=0.8, alpha=0.5)
        ax.barh(y=process, width=duration, left=start,
                color=color_dict[process], edgecolor='black')

    ax.set_xlabel('Time (minutes)')
    bikes_hour = cable_assembler.out_container.level*60/SIM_TIME
    ax.set_title(f'Gantt Chart\nProductivity: {bikes_hour:.2f} bikes/hour')
    ax.grid(axis='x')
    plt.tight_layout()

def count_produced_bikes(data):
    bikes = 0
    for item in data:
        if item['process_id'].startswith('Cable assembler'):
            bikes += 1
    return bikes


def execute_sim(config):
    global cable_assembler
    global process_log

    process_log = [] 
    env = simpy.Environment()
    store = Storage(env)
    env.process(store.request_shipment())
    damper_assemblers = Process_type(env=env, store=store, times=(8,10),
                                    name="Damper assembler", input_stores=("front_fork","damper","damper"), processes_quantity=config[0])
    cutter_welder = Process_type(env=env, store=store, times=(30,45),
                                name="Cutter and welder",
                                input_stores=("tube",),
                                processes_quantity=config[1])
    frame_assemblers = Process_type(env=env, store=store, times=(10,12),
                                    name="Frame assembler",
                                    input_stores=("rear_fork","saddle",damper_assemblers, cutter_welder),
                                    processes_quantity=config[2])
    front_wheel_assemblers = Process_type(env=env, store=store, times=(8,10),
                                    name="Front wheel assembler",
                                    input_stores=("inner_tube","tire","front_rim"),
                                    processes_quantity=config[3])
    rear_wheel_assemblers = Process_type(env=env, store=store, times=(8,10),
                                    name="Rear wheel assembler",
                                    input_stores=("inner_tube","tire","rear_rim"),
                                    processes_quantity=config[4])
    brake_assemblers = Process_type(env=env, store=store, times=(7,9),
                                    name="Brake assembler",
                                    input_stores=(front_wheel_assemblers, "brake"),
                                    processes_quantity=config[5])
    brake_gear_assemblers = Process_type(env=env, store=store, times=(15,20),
                                    name="Brake gear assembler",
                                    input_stores=("sprokets","brake",rear_wheel_assemblers),
                                    processes_quantity=config[6])
    wheels_assemblers = Process_type(env=env, store=store, times=(5,7),
                                    name="Wheels assembler",
                                    input_stores=(frame_assemblers,brake_assemblers,
                                    brake_gear_assemblers), processes_quantity=config[7])
    transmission_assemblers = Process_type(env=env, store=store, times=(10,15),
                                    name="Transmission assembler",
                                    input_stores=(wheels_assemblers,"chain","derailleur","pedals","chain_rings"),
                                    processes_quantity=config[8])
    cable_assembler = Process_type(env=env, store=store, times=(8,12),
                                    name="Cable assembler",
                                    input_stores=("cable","left_control","right_control",transmission_assemblers),
                                    processes_quantity=config[9])
    env.process(stock_monitor(env, store))
    env.run(until=SIM_TIME)

random.seed(RANDOM_SEED)

possible_values = (1,2,3)

combinations = product(possible_values, repeat=10)
record_bikes = 0
for config in combinations:
    execute_sim(config)
    total_bikes = count_produced_bikes(process_log)
    if total_bikes > record_bikes:
        record_bikes = total_bikes
        best_config = config
    elif total_bikes == record_bikes:
        if sum(config) < sum(best_config):
            best_config = config

print(f'Best config: {best_config}')
execute_sim(best_config)
plot_gantt()
plot_occupancy_rate()
plot_inventory_graph()
plt.show()