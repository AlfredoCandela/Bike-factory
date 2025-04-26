import random
import simpy

class Simulator:
    def __init__(self, check_store_time, delivery_time, primary_parts, request_threshold, good_piece_probability, sim_time):
        self.check_store_time = check_store_time
        self.delivery_time = delivery_time
        self.primary_parts = primary_parts
        self.request_threshold = request_threshold
        self.good_piece_probability = good_piece_probability
        self.sim_time = sim_time


    def execute_simulation(self, times_config):
        self.process_log = []
        self.env = simpy.Environment()
        self.store = self.Storage(self)
        self.env.process(self.store.request_shipment(self.process_log))
        self.damper_assemblers = self.Process_type(self, times=(8,10),
                                        name="Damper assembler", input_stores=("front_fork","damper","damper"), processes_quantity=times_config[0])
        self.cutter_welder = self.Process_type(self, times=(30,45),
                                    name="Cutter and welder",
                                    input_stores=("tube",),
                                    processes_quantity=times_config[1])
        self.frame_assemblers = self.Process_type(self, times=(10,12),
                                        name="Frame assembler",
                                        input_stores=("rear_fork","saddle",self.damper_assemblers, self.cutter_welder),
                                        processes_quantity=times_config[2])
        self.front_wheel_assemblers = self.Process_type(self, times=(8,10),
                                        name="Front wheel assembler",
                                        input_stores=("inner_tube","tire","front_rim"),
                                        processes_quantity=times_config[3])
        self.rear_wheel_assemblers = self.Process_type(self, times=(8,10),
                                        name="Rear wheel assembler",
                                        input_stores=("inner_tube","tire","rear_rim"),
                                        processes_quantity=times_config[4])
        self.brake_assemblers = self.Process_type(self, times=(7,9),
                                        name="Brake assembler",
                                        input_stores=(self.front_wheel_assemblers, "brake"),
                                        processes_quantity=times_config[5])
        self.brake_gear_assemblers = self.Process_type(self, times=(15,20),
                                        name="Brake gear assembler",
                                        input_stores=("sprokets","brake",self.rear_wheel_assemblers),
                                        processes_quantity=times_config[6])
        self.wheels_assemblers = self.Process_type(self, times=(5,7),
                                        name="Wheels assembler",
                                        input_stores=(self.frame_assemblers,self.brake_assemblers,
                                        self.brake_gear_assemblers), processes_quantity=times_config[7])
        self.transmission_assemblers = self.Process_type(self, times=(10,15),
                                        name="Transmission assembler",
                                        input_stores=(self.wheels_assemblers,"chain","derailleur","pedals","chain_rings"),
                                        processes_quantity=times_config[8])
        self.cable_assembler = self.Process_type(self, times=(8,12),
                                        name="Cable assembler",
                                        input_stores=("cable","left_control","right_control",self.transmission_assemblers),
                                        processes_quantity=times_config[9])
        self.env.process(self.stock_monitor())
        self.env.run(until=self.sim_time)


    class Storage:
        def __init__(self, simulator):
            self.env = simulator.env
            self.inventory = {}
            self.primary_parts = simulator.primary_parts
            self.request_threshold = simulator.request_threshold
            self.good_piece_probability = simulator.good_piece_probability
            self.check_store_time = simulator.check_store_time
            self.delivery_time = simulator.delivery_time
            for part in self.primary_parts:
                self.inventory[part] = simpy.Container(self.env, init=100, capacity=100)

        def check_level_low(self):
            for part in self.primary_parts:
                if self.inventory[part].level < self.inventory[part].capacity * self.request_threshold/100:
                    return True 
            return False


        def get_good_pieces(self, new_pieces):
            good_pieces = 0
            for i in range(new_pieces):
                if random.randint(1,100) <= self.good_piece_probability:
                    good_pieces += 1
            return good_pieces


        def fill(self):
            #print(f'{env.now} pieces arrived to store')
            for part in self.primary_parts:
                new_pieces = self.inventory[part].capacity - self.inventory[part].level
                good_pieces = self.get_good_pieces(new_pieces)
                if good_pieces>0: yield self.inventory[part].put(good_pieces)
                #print(f'{part} pieces: {self.inventory[part].level}')
            #print('')


        def request_shipment(self, process_log):
            while True:
                yield self.env.timeout(self.check_store_time)
                if self.check_level_low():
                    start_time = self.env.now
                    #print(f'{start_time:.2f} Store under level, requesting pieces')
                    yield self.env.timeout(self.delivery_time)
                    end_time = self.env.now
                    process_log.append({'process_id': "Request shipment",
                                    'start': start_time,
                                    'end': end_time})
                    yield self.env.process(self.fill())


    def stock_monitor(self):
        interval = self.sim_time / 20
        self.stock_log = {"time": []}
        for part in self.store.inventory:
            self.stock_log[part] = []
        
        while True:
            self.stock_log["time"].append(self.env.now)
            for part in self.store.inventory:
                self.stock_log[part].append(self.store.inventory[part].level)

            yield self.env.timeout(interval)


    class Process_type:
        def __init__(self, simulator, times, name, input_stores, processes_quantity):
            self.env = simulator.env
            self.store = simulator.store
            self.process_log = simulator.process_log
            self.times = times
            self.input_stores = input_stores
            self.out_container = simpy.Container(self.env, init=0)

            for i in range(processes_quantity):
                self.env.process(self.process(name + ' ' + str(i+1)))


        def process(self, id_process):
            while True:
                time = random.uniform(*self.times)
                for input in self.input_stores:
                    if type(input) == str:
                        yield self.store.inventory[input].get(1)
                    else:
                        yield input.out_container.get(1)
                        
                
                start_time = self.env.now
                #print(f'{start_time:.2f} {id_process} obtained parts and starts.')
                yield self.env.timeout(time)
                end_time = self.env.now
                yield self.out_container.put(1)
                #print(f'{end_time:.2f} {id_process} finished. Output store: {self.out_container.level}')

                self.process_log.append({'process_id': id_process,
                                        'start': start_time,
                                        'end': end_time})


    def count_produced_bikes(self):
        bikes = 0
        for item in self.process_log:
            if item['process_id'].startswith('Cable assembler'):
                bikes += 1
        return bikes