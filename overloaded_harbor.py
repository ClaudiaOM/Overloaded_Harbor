import simulation as sim
import pandas as pd

class Overloaded_Harbor:

    def __init__(self, number_of_docks = 3):
        self.inf = 1e15
        self.n = number_of_docks
        self.boat = 1
        self.boat_tugboat = 0
        self.min = 0
        # Time
        self.time = 0
        self.time_arrival = self.inf
        self.departure_time = self.inf
        # Arrival time at dock i
        self.time_dock = [self.inf for _ in range(number_of_docks)]
        self.time_dock_min = self.inf
        # Load finished dock i
        self.time_load = [self.inf for _ in range(number_of_docks)]
        self.time_load_min = self.inf
        # Boats in docks
        self.boat_type_dock = [-1 for _ in range(number_of_docks)]
        self.boat_dock=[0 for _ in range(number_of_docks)]
        # Tugboat
        self.time_tugboat = self.inf
        self.tugboat_state = 2
        # Counters
        self.harbor_boats = 0
        self.empty_docks = number_of_docks
        # Dictionaries
        self.arrivals = {}
        self.departures = {}
        self.dock_wait = []
        self.boat_types = {}

        # Time in docks
        self.dock_arrival = {}
        self.dock_departure = {}

    def print_time(self, time):
        hour = time // 60
        min =  time % 60
        d = hour // 24
        if d > 0:
            return f"{int(d)} d {int(hour - d * 24)} :{int(min)}"
        return f"{int(d)} d {int(hour)}:{int(min)}"

    def export_data(self):
        arr = []
        dep = []
        d_arr = []
        d_dep = []
        boats = []
        for i in range(self.boat):
            try:
                if self.departures[i]:
                    arr.append(self.arrivals[i])
                    dep.append(self.departures[i])
                    d_arr.append(self.dock_arrival[i])
                    d_dep.append(self.dock_departure[i])
                    boats.append(self.boat_types[i])
            except:
                continue

        time_dock = [d - a for a, d in zip(d_arr, d_dep)]
        time_harbor = [d - a for a, d in zip(arr, dep)]
        data = {"Boats": boats, "Arrivals": arr, "Dock Arrivals": d_arr, "Dock Departure": d_dep, "Departure": dep,
                "Time in docks": time_dock, "Time in Harbor": time_harbor}
        df = pd.DataFrame(data)
        print(df.to_latex())
        print("AVE dock: " ,sum(time_dock) / len(time_dock))
        print("AVE harbor: " ,sum(time_harbor) / len(time_harbor))
        print(self.boat)
        with open("table.tex", 'w') as f:
            f.write(df.to_latex(index=False))


    # Variable Generation
    def generate_arrival_time(self):
        return sim.exponential(1 / 480)

    def generate_boat_type(self):
        u = sim.uniform(0, 1)
        if u < 0.25:
            return 0  # Small
        elif 0.25 < u < 0.5:
            return 1  # Medium
        else:
            return 2  # Large

    def generate_load_time(self, boat_type):
        if boat_type == 0:
            return sim.normal(9 * 60 , 1)
        elif boat_type == 1:
            return sim.normal(12 * 60 , 2)
        else:
            return sim.normal(18 * 60, 3)

    def generate_harbor_dock_time(self):
        return sim.exponential(1 / 120)

    def generate_dock_harbor_time(self):
        return sim.exponential(1 / 60)

    def generate_tugboat_empty_time(self):
        return sim.exponential(1 / 15)

    def set_min(self):
        self.time_dock_min = min(self.time_dock)
        self.time_load_min = min(self.time_load)
        self.min = min(self.time_arrival, self.time_dock_min, self.time_load_min, self.time_tugboat,
                       self.departure_time)
        self.time = self.min

    def move_boat_to_dock(self):
        boat = self.generate_boat_type()
        tAi = self.time + self.generate_harbor_dock_time()
        self.time_tugboat = tAi
        self.tugboat_state = 3
        self.boat_tugboat = self.boat
        self.boat_types[self.boat] = boat
        for index, b in enumerate(self.boat_type_dock):
            if b == -1:
                print(f"{self.print_time(self.time)}:  Moving boat to dock {index}.")
                self.time_dock[index] = tAi
                self.boat_type_dock[index] = boat
                return

    def manage_arrival_in_harbor(self):
        if self.tugboat_state in {1, 3} \
                or (self.tugboat_state in {0,2} and self.empty_docks == 0):
            print(f"{self.print_time(self.time)}: Boat waiting in Harbor")
            self.harbor_boats += 1
        elif self.tugboat_state == 0 and 0 < self.empty_docks <= self.n:
            self.time_tugboat = self.time + self.generate_tugboat_empty_time()
            print(f"{self.print_time(self.time)}: Tugboat moving to harbor")
            self.tugboat_state = 1
            print(f"{self.print_time(self.time)}:Boat waiting in Harbor")
            self.harbor_boats += 1
        elif self.tugboat_state == 2 and 0 < self.empty_docks <= self.n:
            self.move_boat_to_dock()

        self.boat += 1
        self.time_arrival = self.time + self.generate_arrival_time()
        self.arrivals[self.boat] = self.time_arrival

    def manage_arrival_in_dock(self):
        self.empty_docks -= 1
        for index, time in enumerate(self.time_dock):
            if time == self.time_dock_min:
                self.time_load[index] = self.time + self.generate_load_time(self.boat_type_dock[index])
                self.time_dock[index] = self.inf
                self.boat_dock[index] = self.boat_tugboat
                self.dock_arrival[self.boat_dock[index]] = time
                break

        if len(self.dock_wait) == 0:
            if 0 < self.empty_docks <= self.n and self.harbor_boats > 0:
                self.time_tugboat = self.time + self.generate_tugboat_empty_time()
                print(f"{self.print_time(self.time)}: Tugboat moving to harbor")
                self.tugboat_state = 1
            elif 0 < self.empty_docks <= self.n and self.harbor_boats == 0:
                self.tugboat_state = 0
                print(f"{self.print_time(self.time)}: Tugboat staying in docks")
        else:
            _, _, port = self.dock_wait.pop(0)
            self.time_tugboat = self.time + self.generate_dock_harbor_time()
            self.tugboat_state = 1
            self.boat_tugboat = self.boat_dock[port]
            self.departure_time = self.time_tugboat
            self.empty_docks += 1
            self.dock_departure[self.boat_dock[port]] = self.min
            self.departures[self.boat_dock[port]] = self.departure_time

    def empty_port(self, port):
        print(f"{self.print_time(self.time)}: Emptying dock {port}")
        self.time_dock[port] = self.inf
        self.time_load[port] = self.inf
        self.boat_type_dock[port] = -1

    def manage_load_in_dock(self):
        tci = self.min
        boat = 0
        port = 0
        for index, time in enumerate(self.time_load):
            if time == self.time_load_min:
                boat = self.boat_type_dock[index]
                port = index
                break

        if self.tugboat_state in {1, 2, 3}:
            print(f"{self.print_time(self.time)}: Boat  waiting in dock {port}")
            self.dock_wait.append((tci, boat, port))
            self.empty_port(port)

        elif self.tugboat_state == 0:
            print(f"{self.print_time(self.time)}: Moving boat from dock {port} to harbor.")
            self.time_tugboat = self.time + self.generate_dock_harbor_time()
            self.tugboat_state = 1
            self.boat_tugboat = self.boat_dock[port]
            self.departure_time = self.time_tugboat
            self.empty_docks += 1
            self.dock_departure[self.boat_dock[port]] = self.min
            self.departures[self.boat_dock[port]] = self.departure_time
            if len(self.dock_wait) == 0:
                self.empty_port(port)
            else:
                _, _, port = self.dock_wait.pop(0)
                self.empty_port(port)

    def manage_departure(self):
        self.departure_time = self.inf
        print(f"{self.print_time(self.time)}: Boat leaving harbor")

    def manage_tugboat_time(self):
        if self.tugboat_state == 1:
            self.time_tugboat = self.inf
            if self.harbor_boats == 0:
                self.tugboat_state = 2
            else:
                boat = self.generate_boat_type()
                port = 0

                for index, b in enumerate(self.boat_type_dock):
                    if b == -1:
                        port = index
                        break
                print(f"{self.print_time(self.time)}: Moving boat from harbor queue to dock {port}")
                tAi = self.time + self.generate_harbor_dock_time()
                self.time_tugboat = tAi
                self.time_dock[port] = tAi
                self.boat_type_dock[port] = boat
                self.tugboat_state = 3
                self.boat_tugboat = self.boat - self.harbor_boats
                self.boat_types[self.boat_tugboat] = boat
                self.harbor_boats -= 1
        elif self.tugboat_state in {0, 3}:
            self.tugboat_state = 0
            self.time_tugboat = self.inf

    def simulation(self, simulation_time, export_data = False):
        self.time_arrival = self.generate_arrival_time()
        self.time = self.time_arrival
        self.arrivals[self.boat] = self.time_arrival
        while self.time <= simulation_time:
            self.set_min()
            #print(f"INFO: Harbor Boats {self.harbor_boats}, Tugboat {self.tugboat_state}, Empty Docks {self.empty_docks}")
            if self.time_arrival == self.min:
                print(f"{self.print_time(self.time)}:  Event Arrival in Harbor")
                self.manage_arrival_in_harbor()
            elif self.time_dock_min == self.min:
                print(f"{self.print_time(self.time)}: Event: Arrival in Dock. ")
                self.manage_arrival_in_dock()
            elif self.time_load_min == self.min:
                print(f"{self.print_time(self.time)}: Event: Load Finished in Dock. ")
                self.manage_load_in_dock()
            elif self.departure_time == self.min:
                print(f"{self.print_time(self.time)}: Event: Departure. ")
                self.manage_departure()
            elif self.time_tugboat == self.min:
                #print(f"{self.print_time(self.time)}: Event: Tugboat Arrival. ")
                self.manage_tugboat_time()
        if export_data: self.export_data()


oh = Overloaded_Harbor()
oh.simulation(180 * 24 * 60)
h = []
d = []
for i in range(len(oh.departures)):
    try:
        h.append(oh.departures[i] - oh.arrivals[i])
        d.append(oh.dock_departure[i] - oh.dock_arrival[i])
    except: continue
print(h)
print(sum(h) / len(h))
print(d)
print(sum(d) / len(d))
