from enum import Enum

# TODO: add a Render callback to the App class that will run every tick and
# will handle renders


class Schedule(Enum):
    # def _generate_next_value_(name, start, count, last_values):
    #     return name
    ENTER = 1
    UPDATE = 2
    EXIT = 3


class StateSystems:
    def __init__(self):
        self.on_enter = []
        self.update = []
        self.on_exit = []

    def get_systems(self, schedule: Schedule):
        match schedule:
            case Schedule.ENTER:
                return self.on_enter
            case Schedule.UPDATE:
                return self.update
            case Schedule.EXIT:
                return self.on_exit

    def register_system(self, system, schedule: Schedule):
        match schedule:
            case Schedule.ENTER:
                self.on_enter.append(system)
            case Schedule.UPDATE:
                self.update.append(system)
            case Schedule.EXIT:
                self.on_exit.append(system)


class State:
    def __init__(self, start_state: Enum = None):
        self.state = start_state
        self.schedule = Schedule.ENTER

    # def __repr__(self) -> str:
        # self

    def __str__(self):
        return f"state {self.state.name} is on schedule {self.schedule.name}"


class App:
    def __init__(self, start_state: Enum):
        import esper

        # maps state name to and insace of the State class
        self.systems = {}
        self.global_systems = StateSystems()
        self.state = State(start_state)
        self.next_state = State(start_state)
        self.esper = esper
        # maps look up id to entity. used to get an id to map into self.esper.
        self.entities = {}
        self.quitting = False

    def register(self, state, on=Schedule.UPDATE):
        """
        resisters a system to run in a state. the system will get a reference
        to this class to modify at will.
        """
        def dec(func):
            if state in self.systems:
                self.systems[state].register_system(func, on)
            else:
                loc_state = StateSystems()
                loc_state.register_system(func, on)
                self.systems[state] = loc_state

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return dec

    def c_for_e(self, entity, component):
        """used to get an component value of an entity form the ECS database"""
        e = self.entities.get(entity)

        if e:
            return self.esper.component_for_entity(e, component)
        else:
            return None

    def get_systems(self):
        systems = self.systems.get(self.state.state)

        if systems:
            return systems.get_systems(self.state.schedule)
        else:
            self.state.state = None
            return None

    def set_next_state(self, next_state):
        self.state.schedule = Schedule.EXIT
        self.next_state = State(next_state)

        if self.state.state:
            print("State: ", self.state)

    def exit(self):
        # self.set_next_state(self.state.state)
        # self.next_state = State(self.state.state)
        # self.next_state.schedule = Schedule.EXIT
        # print("self.exit called")
        self.set_next_state(None)
        self.quitting = True

    def step(self):
        # print("current : ", self.state)
        # print("next : ", self.next_state)
        # print("State: ", self.state)

        systems = self.get_systems()

        if systems:
            for f in systems:
                f(self)

        if self.state.schedule is Schedule.ENTER:
            self.state.schedule = Schedule.UPDATE

            if self.state.state:
                print("State: ", self.state)
        elif self.state.schedule is Schedule.EXIT:
            if not self.quitting:
                self.state = self.next_state

                if self.state.state:
                    print("State: ", self.state)

            else:
                self.quitting = False

        elif not systems and self.state.schedule is Schedule.UPDATE:
            self.state.schedule = Schedule.EXIT

            if self.state.state:
                print("State: ", self.state)
        # else:
        #     # print("++++++++++++++++++++")
        #     self.state = self.next_state

    def run(self):
        from time import sleep

        print("State: ", self.state)
        # a system can set state to None to stop this loop and exit.
        while self.state.state is not None:
            self.step()
            sleep(1.0 / 60.0)

        # TODO: add clean up here
