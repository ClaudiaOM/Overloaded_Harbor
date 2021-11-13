import simulation as sim


class Overloaded_Harbor:

    def __init__(self):
        self.inf = 1e15

        self.min = 0
        self.time = 0
        self.time_arrival = self.inf
        self.departure_time = self.inf
        # Arrival time at dock i
        self.time_dock = [self.inf, self.inf, self.inf]
        self.time_dock_min = self.inf
        # Load finished dock i
        self.time_load = [self.inf, self.inf, self.inf]
        self.time_load_min = self.inf
        # Boats in docks
        self.boat_dock = [-1, -1, -1]
        # Tugboat
        self.time_tugboat = self.inf
        self.tugboat_state = 2
        # Counters
        self.harbor_boats = 0
        self.empty_docks = 3
        # Dictionaries
        self.arrivals = []
        self.departures = []
        self.dock_wait = []

    # Variable Generation
    def generate_arrival_time(self):
        return sim.exponential(1/420)

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
            return sim.normal(9, 1)
        elif boat_type == 1:
            return sim.normal(12, 2)
        else:
            return sim.normal(18, 3)

    def generate_harbor_dock_time(self):
        return sim.exponential(1/120)

    def generate_dock_harbor_time(self):
        return sim.exponential(1/60)

    def generate_tugboat_empty_time(self):
        return sim.exponential(1/15)


    def set_min(self):
        self.time_dock_min = min(self.time_dock)
        self.time_load_min = min(self.time_load)
        self.min = min(self.time_arrival, self.time_dock_min, self.time_load_min, self.time_tugboat, self.departure_time)
        self.time = self.min

    # Move boat to dock

    def move_boat_to_dock(self):
        boat = self.generate_boat_type()
        tAi = self.time + self.generate_harbor_dock_time()
        self.time_tugboat = tAi
        self.tugboat_state = 3
        for index, b in enumerate(self.boat_dock):
            if b == -1:
                print(f"{round(self.time,2)}: Moving boat {boat} to dock {index}.")
                self.time_dock[index] = tAi
                self.boat_dock[index] = boat
                return

    def manage_arrival_in_harbor(self):
        #print(f"DEBUG: Harbor {self.harbor_boats},Remolque {self.tugboat_state}, Muelles {self.empty_docks}")
        if self.tugboat_state in {1, 3} \
                or (self.tugboat_state == 2 and self.empty_docks == 0):
            print(f"{round(self.time,2)}: Boat waiting in Harbor")
            self.harbor_boats += 1
        elif self.tugboat_state == 0 and 0 < self.empty_docks < 4:
            self.time_tugboat = self.time + self.generate_tugboat_empty_time()
            print("Tugboat moving to harbor")
            self.tugboat_state = 1
            print("Boat waiting in Harbor")
            self.harbor_boats += 1
        elif self.tugboat_state == 2 and 0 < self.empty_docks < 4:
            self.move_boat_to_dock()

        self.time_arrival = self.time + self.generate_arrival_time()
        self.arrivals.append(self.time_arrival)

    def manage_arrival_in_dock(self):
        self.empty_docks -= 1
        for index, time in enumerate(self.time_dock):
            if time == self.time_dock_min:
                self.time_load[index] = self.time + self.generate_load_time(self.boat_dock[index])
                self.time_dock[index] = self.inf

        if len(self.dock_wait) == 0:
            if 0 < self.empty_docks < 4 and self.harbor_boats > 0:
                self.time_tugboat = self.time + self.generate_tugboat_empty_time()
                print("Tugboat moving to harbor")
                self.tugboat_state = 1
            elif 0 < self.empty_docks < 4 and self.harbor_boats == 0:
                self.tugboat_state = 0
                print("Tugboat staying in docks")

    def empty_port(self, port):
        print(f"Emptying dock {port}")
        self.time_dock[port] = self.inf
        self.time_load[port] = self.inf
        self.boat_dock[port] = -1

    def manage_load_in_dock(self):
        tci = self.min
        boat = 0
        port = 0
        for index, time in enumerate(self.time_load):
            if time == self.time_load_min:
                boat = self.boat_dock[index]
                port = index
                break

        if self.tugboat_state in {1,2,3}:
            print(f"Boat {boat} waiting in dock {port}")
            self.dock_wait.append((tci, boat, port))
            self.empty_port(port)

        elif self.tugboat_state == 0:
            self.time_tugboat = self.time + self.generate_dock_harbor_time()
            print(f"Moving boat {boat} from dock to harbor.")
            self.tugboat_state = 1
            self.departure_time = self.time_tugboat
            self.empty_docks += 1
            if len(self.dock_wait) == 0:
                self.empty_port(port)
            else:
                _, _, port = self.dock_wait.pop(0)
                self.empty_port(port)

    def manage_departure(self):
        self.departures.append(self.time_tugboat)
        self.departure_time = self.inf
        print(f"Boat leaving at time {round(self.time_tugboat,2)}")

    def manage_tugboat_time(self):
        if self.tugboat_state == 1:
            self.time_tugboat = self.inf
            if self.harbor_boats == 0:
                self.tugboat_state = 2
            else:
                print("Moving boat form harbor queue to dock")
                boat = self.generate_boat_type()
                port = 0

                for index,b in enumerate(self.boat_dock):
                    if b == -1:
                        port = index
                        break

                tAi = self.time + self.generate_harbor_dock_time()
                self.time_tugboat = tAi
                self.time_dock[port] = tAi
                self.boat_dock[port] = boat
                self.tugboat_state = 3
                self.harbor_boats -= 1
        elif self.tugboat_state in {0,3}:
            self.tugboat_state = 0
            self.time_tugboat = self.inf

    def simulation(self, simulation_time):
        self.time_arrival = self.generate_arrival_time()
        self.time = self.time_arrival

        while self.time <= simulation_time:
            self.set_min()

            print(f"DEBUG: Harbor Boats {self.harbor_boats}, Tugboat {self.tugboat_state}, Empty Docks {self.empty_docks}")
            if self.time_arrival == self.min:
                print(f"{round(self.time,2)} : Event Arrival in Harbor")
                self.manage_arrival_in_harbor()
            elif self.time_dock_min == self.min:
                print(f"{round(self.time,2)} :Event: Arrival in Dock. ")
                self.manage_arrival_in_dock()
            elif self.time_load_min == self.min:
                print(f"{round(self.time,2)} :Event: Load Finished in Dock. ")
                self.manage_load_in_dock()
            elif self.departure_time == self.min:
                print(f"{round(self.time,2)} :Event: Departure. ")
                self.manage_departure()
            elif self.time_tugboat == self.min:
                print(f"{round(self.time,2)} :Event: Tugboat Arrival. ")
                self.manage_tugboat_time()


oh = Overloaded_Harbor()
oh.simulation(92*60)
print(len(oh.arrivals),len(oh.departures))
