import random
import simpy
import matplotlib.pyplot as plt
import seaborn as sns

SIM_TIME = 200
PROB_FAIL_TEST = 10 # From 1 to 100
GOOD_PIECE_PROBABILITY = 90 # Probability for a new piece to not be discarded
REQUEST_THRESHOLD = 50 # Expressed in %. Quantity of pieces in store to buy more parts
DELIVERY_TIME = 100 # For shipment
ASSEMBLY_TIME = 5
WIELD_TIME = 20
TEST_TIME = 2
UNWELD_TIME = 5
PACKAGE_TIME = 5
PCBS_PER_WIELD = 5 # Batch size for wield process
PCBS_PER_PACK = 10 # Batch size for packaging process

RANDOM_SEED = 42


gantt_data = []
def log_event(process_name, start, end):
    gantt_data.append({
        'Process': process_name,
        'Start': start,
        'Finish': end
    })

def plot_gantt(data):
    sns.set_theme(style='ticks', context='talk')

    unique_processes = list(set(item['Process'] for item in data))
    palette = sns.color_palette('Set3', n_colors=len(unique_processes))
    color_dict = {process: palette[i] for i, process in enumerate(unique_processes)}

    fig, ax = plt.subplots(figsize=(12, 6))
    for item in data:
        process = item['Process']
        start = item['Start']
        finish = item['Finish']
        duration = finish - start
        ax.axvline(x=start, color='gray', linewidth=0.8)
        ax.axvline(x=finish, color='gray', linewidth=0.8)
        ax.barh(y=process, width=duration, left=start,
                color=color_dict[process], edgecolor='black')

    ax.set_xlabel('Time (minutes)')
    ax.set_title('Process Gantt Chart')
    plt.tight_layout()
    plt.show()


class Storage:
    def __init__(self, env):
        self.store_a = simpy.Container(env, init=30, capacity=30)
        self.store_b = simpy.Container(env, init=20, capacity=20)
        self.store_c = simpy.Container(env, init=10, capacity=10)
        self.env = env
    
    def check_level_low(self):
        a_under_level = self.store_a.level < self.store_a.capacity * REQUEST_THRESHOLD/100
        b_under_level = self.store_b.level < self.store_b.capacity * REQUEST_THRESHOLD/100
        c_under_level = self.store_c.level < self.store_c.capacity * REQUEST_THRESHOLD/100

        if a_under_level or b_under_level or c_under_level:
            return True
        else:
            return False

    def get_good_pieces(self, new_pieces):
        good_pieces = 0
        for i in range(new_pieces):
            if random.randint(1,100) <= GOOD_PIECE_PROBABILITY:
                good_pieces += 1
        
        return good_pieces


    def fill(self):
        new_pieces_a = self.store_a.capacity - self.store_a.level
        new_pieces_b = self.store_b.capacity - self.store_b.level
        new_pieces_c = self.store_c.capacity - self.store_c.level

        good_pieces_a = self.get_good_pieces(new_pieces_a)
        good_pieces_b = self.get_good_pieces(new_pieces_b)
        good_pieces_c = self.get_good_pieces(new_pieces_c)

        yield self.store_a.put(good_pieces_a)
        yield self.store_b.put(good_pieces_b)
        yield self.store_c.put(good_pieces_c)
        print(f'{env.now} pieces arrived to store')
        print(f'A pieces: {self.store_a.level}')
        print(f'B pieces: {self.store_b.level}')
        print(f'C pieces: {self.store_c.level}')

    def request_pieces(self):
        print(f'{env.now} Starting process to get pieces from store')

        yield self.store_a.get(3)
        yield self.store_b.get(2)
        yield self.store_c.get(1)
    
        print(f'{env.now} Pieces obtained from store. Current stock:')
        print(f'A: {self.store_a.level} pieces')
        print(f'B: {self.store_b.level} pieces')
        print(f'C: {self.store_c.level} pieces')

    def request_shipment(self):
        check_time = 1
        while True:
            yield self.env.timeout(check_time)
            if self.check_level_low():
                start = env.now
                print(f'{start} Store under level, requesting pieces')
                yield self.env.timeout(DELIVERY_TIME)
                yield self.env.process(self.fill())
                end = env.now
                log_event('Shipment', start, end)


def assembly(env, store, assembled_store):
    while True:
        yield env.process(store.request_pieces())
        start = env.now
        print(f'{start} start assembly')
        yield env.timeout(ASSEMBLY_TIME)
        yield assembled_store.put(1)
        end = env.now
        print(f'{end} Assembly finished. {assembled_store.level} pcbs waiting')
        log_event('Assembly', start, end)


def wield(env, assembled_store, wield_store):
    while True:
        yield assembled_store.get(PCBS_PER_WIELD)
        start = env.now
        print(f'{start} Starting wield')
        yield env.timeout(WIELD_TIME)
        end = env.now
        print(f'{end} Wield finished')
        log_event('Wield', start, end)
        yield wield_store.put(PCBS_PER_WIELD)
        print(f'{env.now} Welded pcbs: {wield_store.level}')

def test(env, wield_store, ok_store, no_ok_store):
    while True:
        yield wield_store.get(1)
        start = env.now
        print(f'{start} Starting test')
        yield env.timeout(TEST_TIME)
        end = env.now
        log_event('Test', start, end)
        if random.randint(1,100) <= PROB_FAIL_TEST:
            print(f'{end} Test failed')
            yield no_ok_store.put(1)
        else:
            print(f'{end} Test passed')
            yield ok_store.put(1)

def unweld(env, no_ok_store, assembled_store):
    while True:
        yield no_ok_store.get(1)
        start = env.now
        print(f'{start} Starting unweld')
        yield env.timeout(UNWELD_TIME)
        end = env.now
        log_event('Unweld', start, end)
        print(f'{end} Unweld finished')
        yield assembled_store.put(1)

def package(env, ok_store):
    pcbs_finished = 0
    while True:
        yield ok_store.get(PCBS_PER_PACK)
        start = env.now
        print(f'{start} Starting package')
        yield env.timeout(PACKAGE_TIME)
        end = env.now
        log_event('Package', start, end)
        pcbs_finished += PCBS_PER_PACK
        print(f'{end} Package finished. Total pcbs: {pcbs_finished}')

random.seed(RANDOM_SEED)
env = simpy.Environment()

store = Storage(env)
assembled_store = simpy.Container(env, init=0)
wield_store = simpy.Container(env, init=0)
ok_store = simpy.Container(env, init=0)
no_ok_store = simpy.Container(env, init=0)

env.process(store.request_shipment())
env.process(assembly(env, store, assembled_store))
env.process(wield(env, assembled_store, wield_store))
env.process(test(env, wield_store, ok_store, no_ok_store))
env.process(unweld(env, no_ok_store, assembled_store))
env.process(package(env, ok_store))

print('PCB Factory')
env.run(until=SIM_TIME)

plot_gantt(gantt_data)