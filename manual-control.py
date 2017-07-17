#!/usr/bin/env python

from sumd_receiver import SumdReceiver
from simple_console import SimpleConsole
from threading import Thread
from time import sleep

"""
We define this shared class that is passed from our main thread to our
receiver update thread so that we can tell the update thread when to exit
by updating the value in our class from the main thread.
"""
class FinishedMarker:
    is_finished = False

"""
Continually sends updated values from the controller.  This function
is expected to be invoked as another thread in order to constantly
send values while separating the logic of calculating those values to the
main thread waiting for user input from the console.
"""
def bg_send_updated_controller_values(receiver, finished_test):
    while finished_test.is_finished == False:
        receiver.send_current_values()        
        sleep(.05)

if __name__ == "__main__":
    finished_test = FinishedMarker()

    receiver = SumdReceiver("/dev/ttyAMA0")

    thread = Thread(target=bg_send_updated_controller_values, args=(receiver, finished_test))
    thread.start()

    try:
        throttle_inc = 20
        pitch_inc = 10
        roll_inc = 10
        while True:
            character = SimpleConsole.get_next_character()
            if character == 'v' or character == 'c':
                receiver.arm() 
            elif character == 'b':
                receiver.disarm()
            elif character == 'w':
                receiver.update_receiver_values(pitch = receiver.pitch + pitch_inc)
            elif character == 'a':
                receiver.update_receiver_values(roll = receiver.roll - roll_inc)
            elif character == 's':
                receiver.update_receiver_values(pitch = receiver.pitch - pitch_inc)
            elif character == 'd':
                receiver.update_receiver_values(roll = receiver.roll + roll_inc)
            elif character == 'i':
                receiver.update_receiver_values(throttle = receiver.throttle + throttle_inc)
            elif character == 'k':
                receiver.update_receiver_values(throttle = receiver.throttle - throttle_inc)
            elif character == 'x' or character == 'z':
                receiver.disarm()

                # Wait a little while so that we send the same command multiple times.  This is
                # required because the drone will only accept a command if it is sent at least 4
                # times in a second.  If we immediately return, it will not pick up the new value
                # and thus will not disarm.
                sleep(.5)
                break
    finally:
       finished_test.is_finished = True 
