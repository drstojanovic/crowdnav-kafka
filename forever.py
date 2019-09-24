# this starts the simulation (int parameters are used for parallel mode)
from app import Boot
from time import sleep

if __name__ == "__main__":
    sleep(12)
    Boot.start(0, False, True)