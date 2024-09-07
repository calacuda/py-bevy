from enum import Enum
from joblib import Parallel, delayed
from logging import INFO
from py_bevy._logging import get_logger

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
    def __init__(self, start_state: Enum, log_level=INFO):
        import esper

        # maps state name to and insace of the State class.
        self.systems = {}
        # systems that apply to all states.
        self.global_systems = StateSystems()
        self._state = State(start_state)
        self._next_state = State(start_state)
        self.esper = esper
        # maps look up id to entity. used to get an id to map into self.esper.
        self.entities = {}
        self._quitting = False
        self._par = Parallel(-1, require='sharedmem')
        self.log = get_logger(log_level)

    # def debug(self, *args, **kwargs):
    #     self.logger.debug(*args, **kwargs)
    #
    # def info(self, *args, **kwargs):
    #     self.logger.info(*args, **kwargs)
    #
    # def warning(self, *args, **kwargs):
    #     self.logger.warning(*args, **kwargs)
    #
    # def error(self, *args, **kwargs):
    #     self.logger.error(*args, **kwargs)
    #
    # def critical(self, *args, **kwargs):
    #     self.logger.critical(*args, **kwargs)

    def set_loglevel(self, log_level):
        self.logger = get_logger(log_level)

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
                self.log.debug(f"System, {func.__name__} running...")
                val = func(*args, **kwargs)
                self.log.debug(
                    f"System, {func.__name__} compleated without error")

                return val

            self.log.info(f"\"{func.__name__}\" registered to run on, \"{
                on}\" in \"{state}\".")

            return wrapper
            # return func

        return dec

    def c_for_e(self, entity, component):
        """used to get an component value of an entity form the ECS database"""
        e = self.entities.get(entity)

        if e:
            return self.esper.component_for_entity(e, component)
        else:
            return None

    def get_systems(self):
        systems = self.systems.get(self._state.state)

        if systems:
            return systems.get_systems(self._state.schedule)
        else:
            self._state.state = None
            return None

    def set_next_state(self, next_state):
        self._state.schedule = Schedule.EXIT
        self._next_state = State(next_state)

        if self._state.state:
            self.log.debug(f"State set to: {self._state}")

    def exit(self):
        # self.set_next_state(self.state.state)
        # self.next_state = State(self.state.state)
        # self.next_state.schedule = Schedule.EXIT
        # print("self.exit called")
        self.log.debug("applicaiton exit has been called.")
        # self.set_next_state(None)
        self._quitting = True
        self.log.warning("applicaiton exit has been scheduled.")

    def step(self):
        # print("current : ", self.state)
        # print("next : ", self.next_state)
        # print("State: ", self.state)
        if self._quitting:
            self.log.debug("preparing to quit")
            # self._quitting = False
            self.set_next_state(None)

        systems = self.get_systems()

        if systems:
            # for f in systems:
            #     f(self)
            # Parallel(-1, require='sharedmem')(delayed(f)(self)
            #                                   for f in systems)
            self._par(delayed(f)(self)
                      for f in systems)

        if self._state.schedule is Schedule.ENTER:
            # print(f"schedule was ENTER and self.quitting = {self.quitting}")

            self._state.schedule = Schedule.UPDATE

            if self._state.state:
                self.log.debug(f"State set to: {self._state}")
        elif self._state.schedule is Schedule.EXIT:
            print(f"schedule was EXIT and self.quitting = {self._quitting}")
            self._state = self._next_state

            if self._state.state:
                self.log.debug(f"State set to: {self._state}")

            # if not self._quitting:
            #                 else:

            # print(f"state = {self.state.state} | next_state = {
            #       self.next_state}")
        elif not systems and self._state.schedule is Schedule.UPDATE:
            # print(f"schedule was UPDATE | self.quitting = {
            #     self.quitting} | no systems found")

            self._state.schedule = Schedule.EXIT

            if self._state.state:
                self.log.debug(f"State set to: {self._state}")
        # else:
        #     # print("++++++++++++++++++++")
        #     # print(f"schedule was {self._state.schedule} | state.name = {
        #     #       self._state.state} | self.quitting = {self._quitting}")
        #     # print(f"next_state = {self._next_state}")
        #     # print("++++++++++++++++++++")
        #
        #     self._state = self._next_state

    def run(self):
        # from time import sleep

        self.log.debug(f"State set to: {self._state}")
        # a system can set state to None to stop this loop and exit.
        while self._state.state is not None:
            self.step()
            # sleep(1.0 / 60.0)

        self.log.warning("application main loop has run to completion")

        # TODO: add clean up here
