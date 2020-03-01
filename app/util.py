""" Helper functions """
import time


def add_to_average(total_count, total_value, new_value):
    """ simple sliding average calculation """
    return ((1.0 * total_count * total_value) + new_value) / (total_count + 1)


def current_milli_time():
    return int(round(time.time() * 1000))
