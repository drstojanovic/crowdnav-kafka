from app.config import Config

from app.entity.car import Car


class NullCar:
    """ a car with no function used for error prevention """
    def __init__(self):
        pass

    def set_arrived(self, tick):
        pass


class CarRegistry(object):
    """ central registry for all our cars we have in the sumo simulation """

    # always increasing counter for carIDs
    car_index_counter = 0
    # map of all cars
    cars = {}
    # counts the number of finished trips
    total_trips = 0
    # average of all trip durations
    total_trip_average = 0
    # average of all trip overheads (overhead is TotalTicks/PredictedTicks)
    total_trip_overhead_average = 0

    @classmethod
    def apply_car_counter(cls):
        """ syncs the value of the carCounter to the SUMO simulation """
        while len(CarRegistry.cars) < Config().sumo_total_cars:
            cls.car_index_counter += 1
            c = Car("car-" + str(CarRegistry.car_index_counter))
            cls.cars[c.id] = c
            c.add_to_simulation(0)
        while len(CarRegistry.cars) > Config().sumo_total_cars:
            # to many cars -> remove cars
            (k, v) = CarRegistry.cars.popitem()
            v.remove()

    @classmethod
    def find_by_id(cls, car_id):
        """ returns a car by a given carID """
        try:
            return CarRegistry.cars[car_id]
        except:
            return NullCar()

    @classmethod
    def process_tick(cls, tick):
        """ processes the simulation tick on all registered cars """
        for key in CarRegistry.cars:
            CarRegistry.cars[key].process_tick(tick)
