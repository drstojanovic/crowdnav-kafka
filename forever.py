# this starts the simulation (int parameters are used for parallel mode)
from app import boot
from time import sleep

if __name__ == "__main__":
    sleep(10)
    boot.start(0, False, True)
