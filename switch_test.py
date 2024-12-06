import neopixel
from machine import Pin, Timer

# NeoPixel configuration
num_pixels = 1  # Number of NeoPixels
neo_pin = 13    # Pin connected to the NeoPixel
np = neopixel.NeoPixel(machine.Pin(neo_pin), num_pixels)


# Define Relay configurations for limit switches
Limit_Switch_Closed_Pin = 0
Limit_Switch_Closed = Pin(Limit_Switch_Closed_Pin, Pin.IN, machine.Pin.PULL_UP)

Limit_Switch_Open_Pin = 1
Limit_Switch_Open = Pin(Limit_Switch_Open_Pin, Pin.IN, machine.Pin.PULL_UP)

# Function to set NeoPixel color
def set_neopixel_color(color):
    neopixel_red = ((255,0,0))
    neopixel_green = ((0,255,0))
    neopixel_blue = ((0,0,255))
    if color == "red":
        np[0] = neopixel_red
    elif color == "green":
        np[0] = neopixel_green
    elif color == "blue":
        np[0] = neopixel_blue
    np.write()

def Get_Limit_Switch_Values():
    global LS_door_closed_state
    global LS_door_open_state
    LS_door_open_state = Limit_Switch_Open.value()
    LS_door_closed_state = Limit_Switch_Closed.value()

# DoorClosing.py
def Door_Closed_Handler(pin):
    global LS_door_closed_state
    global LS_door_open_state
    # If the closed door limit switch is closed, then update the limit switch states and turn off the motor.
    if (Limit_Switch_Open.value()==1):
        # Turn off handler to prevent re-introduce multiple interrupts while running
        Limit_Switch_Closed.irq(handler=None)
        # Update global variables with current state of limit switches
        LS_door_closed_state = Limit_Switch_Closed.value()
        LS_door_open_state = Limit_Switch_Open.value()
        print("Door closed limit switch value is -- %i" % LS_door_closed_state)
    
    
#DoorOpen.py
def Door_Open_Handler(pin):
    global LS_door_open_state
    global LS_door_closed_state
    # If the open door limit switch is closed, then update the limit switch states and turn off the motor.
    if (Limit_Switch_Open.value()==1):
        # Turn off handler to prevent re-introduce multiple interrupts while running
        Limit_Switch_Open.irq(handler=None)
       # Update global variables with current state of limit switches
        LS_door_open_state = Limit_Switch_Open.value()
        LS_door_closed_state = Limit_Switch_Closed.value()
        print("Door open limit switch value is -- %i" % LS_door_open_state)


# Create Closed Limit Switch Handler for both falling and rising
Limit_Switch_Closed.irq(trigger=machine.Pin.IRQ_FALLING, handler = Door_Closed_Handler)

# Create Open Limit Switch Handler for both falling and rising
Limit_Switch_Open.irq(trigger=machine.Pin.IRQ_FALLING, handler = Door_Open_Handler)


LS_door_closed_state = Limit_Switch_Closed.value()
print("Door closed limit switch current value = ", LS_door_closed_state)
LS_door_open_state = Limit_Switch_Open.value()
print("Door open limit switch current value = ", LS_door_open_state)