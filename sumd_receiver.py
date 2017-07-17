#!/usr/bin/env python

from __future__ import with_statement 
import serial, time, struct, threading

class SumdReceiver:
    pitch = 1500
    yaw = 1500
    roll = 1500
    # Note that this value is contextual to the flight controller.  In order to be able to arm in, say,
    # cleanflight / betaflight, you must ensure your initial throttle value is low enough (when arming
    # via aux).  Otherwise it may not arm.
    throttle = 1040
    aux1 = 1500
    lock = threading.Lock()

    def __init__(self, serPort):
        self.ser = serial.Serial()
        self.ser.port = serPort
        self.ser.baudrate = 115200
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_EVEN
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 0
        self.ser.xonxoff = False
        self.ser.rtscts = False
        self.ser.dsrdtr = False
        self.ser.writeTimeout = 0

        try:
            self.ser.open()
        except Exception, error:
            print "Error opening port " + self.ser.port + ": " + str(error)
            raise;

    """
    A 16 bit Cyclic Redundancy Check function.  Given the input message, calculates
    a 16 bit number that can be used as an additional check to ensure that the message
    on the receiving side is the same that was transmitted.  I'm not aware of the
    significance of much of the algorithm below, but think of it like a cheap hash function
    that can only protect against accidental and not malicious tampering of the data.
    """
    def getCrc(self, message):
        #CRC-16-CITT poly, used also by the SUMD protocol.
        poly = 0x1021

        crc = 0

        for byte in message:
            crc = crc ^ ord(byte) << 8
            for i in range(0, 8):
                if crc & 0x8000 != 0:
                    crc = (crc << 1) ^ poly
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return crc

    """
    This function is called outside of the expected update loop in order to update any values
    being sent to the receiver.  It automatically locks so that there is no threading issue
    during the update.
    """
    def update_receiver_values(self, roll=None, pitch=None, yaw=None, throttle=None, aux1=None):
        with self.lock:
            if roll != None:
                self.roll = roll
            if pitch != None:
                self.pitch = pitch
            if yaw != None:
                self.yaw = yaw
            if throttle != None:
                self.throttle = throttle
            if aux1 != None:
                self.aux1 = aux1

    """
    This function sends the current values stored in this receiver to the flight
    controller.  This function should regularly be called in the main loop so that
    the flight controller does not go into "failsafe" mode.  Even if the
    values remain the same as the last time they were called.
    """
    def send_current_values(self):
        data = []
        with self.lock:
            data = [self.roll, self.pitch, self.throttle, self.yaw, self.aux1]
        self.send_raw_data(data)

    """ 
    This function sends raw data to the receiver in the SUMD format.  Implicitly assumes the 
    data is in the format of an array of values between 1000 and 2000 (the min and max
    assumed to be set on the flight controller).
    """
    def send_raw_data(self, data):
        # First multiply every value by 8.  This is because the SUMD protocol has a 
        # different range than that which is expected from the flight controller.
        data = [elem * 8 for elem in data]

        # Now we start with a few values: the SUMD header, and then a differentiator 
        # between SUMD and SUMH.  And then the length of the data and the data.
        SUMD_HEADER_ID = 0xA8
        SUMD_ID_SUMD = 0x01
        total_data = [SUMD_HEADER_ID, SUMD_ID_SUMD, len(data)] + data

        # We create an initial packed data representation of the data so far, so
        # that we can create a CRC checksum of the data.  The CRC checksum ensures
        # in the controller that the data received is what we sent.
        packed_data = struct.pack('>3B%dH' % len(data), *total_data)

        total_data.append(self.getCrc(packed_data))

        # Now we pack the data again with the CRC appended and we send it off.
        to_print = struct.pack('>3B%dHH' % len(data), *total_data)
        self.ser.write(to_print)

    """
    The following helper functions are specific to setup defined in the flight controller
    software.  Aux values were designated to arm and disarm the copter, and to set
    different modes of flight.  These would need to be replicated on the flight controller
    in order for these to perform their below functions.
    """

    """
    This function is used to arm the flight controller.  This must be invoked before any
    other commands are sent to the flight controller.  Presumably, this exists because in 
    the usual case, there is someone explicitly controlling the drone with a joystick.  And
    it may not do to turn on the drone and immediately have whatever state of the joysticks
    sending the drone in an arbitrary direction.  So there was an additional step added to 
    force the joystick to explicitly 'arm' the drone before the movement of the joysticks is
    interpretted as commands.
    """
    def arm(self):
        self.update_receiver_values(aux1=1650)

    """
    This function disarms the drone.  Because we are sending commands as a serial receiver, there is
    no explicit reason to invoke this function.  We can use any number of ways to prevent the sending
    of data to our flight controller if we wish.  But note here that we can change the aux value and 
    thereby change the mode.  See the arm function for more verbose documentation on why the below commands.
    """
    def disarm(self):
        self.update_receiver_values(aux1=1500)

    """
    This function disarms the drone.  Because we are sending commands as a serial receiver, there is
    no explicit reason to invoke this function.  We can use any number of ways to prevent the sending
    of data to our flight controller if we wish.  But note here that we can change the aux value and 
    thereby change the mode.  See the arm function for more verbose documentation on why the below commands.
    """
    def set_flight_mode(self):
        self.update_receiver_values(aux1=1750)
