from umqtt.simple import MQTTClient
import time
import network
import neopixel
import secrets
from machine import Pin, Timer

# Define WiFi and MQTT details
WIFI_SSID = secrets.WIFI_SSID
WIFI_PASS = secrets.WIFI_PASS
MQTT_BROKER = secrets.MQTT_BROKER
MQTT_USERNAME = secrets.MQTT_USERNAME
MQTT_PASSWORD = secrets.MQTT_PASSWORD
MQTT_TOPIC_REQUEST = secrets.MQTT_TOPIC_REQUEST


# NeoPixel configuration
num_pixels = 1  # Number of NeoPixels
neo_pin = 13    # Pin connected to the NeoPixel
np = neopixel.NeoPixel(machine.Pin(neo_pin), num_pixels)

# Define Relay configurations for limit switches
Limit_Switch_Closed_Pin = 0
Limit_Switch_Closed = Pin(Limit_Switch_Closed_Pin, Pin.IN, machine.Pin.PULL_UP)

Limit_Switch_Open_Pin = 1
Limit_Switch_Open = Pin(Limit_Switch_Open_Pin, Pin.IN, machine.Pin.PULL_UP)

# Motor assignments
Relay_A_Pin = 14
Relay_B_Pin = 15

# Relay_A = Door Closing
Relay_A = Pin(Relay_A_Pin, Pin.OUT)
# Relay_B = Door Opening
Relay_B = Pin(Relay_B_Pin, Pin.OUT)

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

# Variables to track the current door state and desired door state
current_door_state = ""

# Old Style: Door Limit Switch State Variables - start at 0 until polled on message change
# LS_door_closed_state = 0
# LS_door_open_state = 0

# Get state for limit switches
# 0 = switch is closed
# 1 = switch is open
LS_door_closed_state = Limit_Switch_Closed.value()
print("Door closed limit switch current value = ", LS_door_closed_state)
LS_door_open_state = Limit_Switch_Open.value()
print("Door open limit switch current value = ", LS_door_open_state)


# Initialize WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

# Wait for the WiFi connection to be established
while not wifi.isconnected():
    time.sleep(1)

# Initialize MQTT client
client = MQTTClient("micropython_client", MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)

# Possibly unused code - schedule for removal.
def Get_Limit_Switch_Values():
    global LS_door_closed_state
    global LS_door_open_state
    LS_door_open_state = Limit_Switch_Open.value()
    LS_door_closed_state = Limit_Switch_Closed.value()


def Turn_On_Handlers():
    Limit_Switch_Closed.irq(handler=Door_Open_Handler)
    Limit_Switch_Open.irq(handler=Door_Closed_Handler)
#    print("Turn_On_Handler function hit - handlers are back on! %s" % Limit_Switch_Closed)


# DoorClosing.py
def Door_Closed_Handler(pin):
    global LS_door_closed_state
    global LS_door_open_state
    # If the closed door limit switch is closed, then update the limit switch states and turn off the motor.
    if (Limit_Switch_Open.value() == 1):
        # Turn off handler to prevent re-introduce multiple interrupts while running
        Limit_Switch_Open.irq(handler=None)
        # Update global variables with current state of limit switches
        LS_door_closed_state = Limit_Switch_Closed.value()
        LS_door_open_state = Limit_Switch_Open.value()
        # Motor gets turned off
        MotorOff("Door_Closed_Handler")
        # Turn the interrupt handlers back on
        Turn_On_Handlers()
        print("Door closed limit switch value is -- %i" % LS_door_closed_state)
    
    
#DoorOpen.py
def Door_Open_Handler(pin):
    global LS_door_open_state
    global LS_door_closed_state
    # If the open door limit switch is closed, then update the limit switch states and turn off the motor.
    if (Limit_Switch_Closed.value() == 1):
        # Turn off handler to prevent re-introduce multiple interrupts while running
        Limit_Switch_Closed.irq(handler=None)
       # Update global variables with current state of limit switches
        LS_door_open_state = Limit_Switch_Open.value()
        LS_door_closed_state = Limit_Switch_Closed.value()
        # Motor gets turned off
        MotorOff("Door_Open_Handler")
        # Turn the interrupt handlers back on
        Turn_On_Handlers()
        print("Door open limit switch value is -- %i" % LS_door_open_state)
        

# Create Closed Limit Switch Handler for both falling and rising
# Limit_Switch_Closed.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler = Door_Closed_Handler)
# Limit_Switch_Closed.irq(trigger=machine.Pin.IRQ_FALLING, handler = Door_Closed_Handler)

# Handler to detect when the closed switch is open which represents the door itself is OPEN and in an UP position
Limit_Switch_Closed.irq(trigger=machine.Pin.IRQ_RISING, handler = Door_Open_Handler)

# Create Open Limit Switch Handler for both falling and rising
# Limit_Switch_Open.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler = Door_Open_Handler)
# Limit_Switch_Open.irq(trigger=machine.Pin.IRQ_FALLING, handler = Door_Open_Handler)

# Handler to detect when the open limit switch is open which represents the door itself is CLOSED and in a DOWN position
Limit_Switch_Open.irq(trigger=machine.Pin.IRQ_RISING, handler = Door_Closed_Handler)

# Turn the motor off
def MotorOff(sending_func):
    print("Motor off function fired from %s." % sending_func)
    Relay_A.value(0)
    Relay_B.value(0)

# MQTT Message Received
def on_message(topic, msg):
    #Turning this to blue for indicator that message was received
    set_neopixel_color("blue")
    global current_door_state
        
    #Decode the desired state from MQTT Topic:
    new_desired_state = msg.decode("utf-8")
    print("New Desired State Message Received %s" % new_desired_state)
    
    # Check limit switches for door state 
    if Limit_Switch_Closed.value() == 0 and Limit_Switch_Open.value() == 1:
        print("Limit switches polled - door is currently Closed")
        current_door_state = "Closed"
    elif Limit_Switch_Closed.value() == 1 and Limit_Switch_Open.value() == 0:
        current_door_state = "Open"
        print("Limit switches polled - door is currently Open")
    elif Limit_Switch_Closed.value() == 0 and Limit_Switch_Open.value() == 0:
        current_door_state = "Unknown"
        print("Both limit switchs are open -- door in unknown state")
    # Commenting this out as both switches will be closed while door is transitioning
    # elif Limit_Switch_Closed.value() == 1 and Limit_Switch_Open.value() == 1:
    #     current_door_state = "Unknown"
    #     print("Both limit switchs are open -- door in unknown state")
    
    # Only check the current door state
    if new_desired_state == "door_check":
        door_state_msg = "I checked the limit switches and the door is currently: %s" % current_door_state
        client.publish("from_the_door",door_state_msg)
    # Check if door is in the desired state already - if yes, don't do anything.
    if new_desired_state == current_door_state:
        print("Door is already in desired state %s" % current_door_state)
        if current_door_state == "Closed":
            set_neopixel_color("red")
        elif current_door_state == "Open":
            set_neopixel_color("green")
    # Complicated IF statement - only move the door if the state is not equal to current and door_check was not submitted to the topic
    elif new_desired_state != current_door_state and new_desired_state != "door_check":
        # Door is not in desired state, moving...
        move_door(new_desired_state)

# Function to turn on the motor and move the door
def move_door(desired_state):
    global LS_door_closed_state
    global LS_door_open_state

    # Relay gets flipped here - motor turning
    print("Door is moving to state: %s" % desired_state)
    print("Checking LS_door_closed_state == %i" % LS_door_closed_state)
    print("Checking LS_door_open_sate == %i" % LS_door_open_state)
    if desired_state == "Open":
        print("Motor on: opening")
        # time.sleep(1)
        set_neopixel_color("green")
        #Turn off closed limit switch handler to prevent throwing an interrupt from the closed limit switch when it is opened while the door is moving
        Limit_Switch_Open.irq(handler=None)
        Relay_A.value(1)
        Relay_B.value(0)
        #Wait for door to finish
        try:
            # While the closed limit switch is closed
            while Limit_Switch_Closed.value() == 0:    
                print("Waiting for interrupt request from door open limit switch...")
                time.sleep(1)
        except Exception as e:
            MotorOff("move_door open exception")
            print(e)
    elif desired_state == "Closed":
        print("Motor on: closing")
        # time.sleep(3)
        #Turn off open limit switch handler to prevent throwing an interrupt from the open limit switch when it is opened while the door is moving
        Limit_Switch_Closed.irq(handler=None)
        Relay_A.value(0)
        Relay_B.value(1)
        set_neopixel_color("red")
        #Wait for door to finish
        try:
            # While the open limit switch open
            while Limit_Switch_Open.value() == 0:    
                print("Waiting for interrupt request from door closed limit switch...")
                time.sleep(1)
        except Exception as e:
            MotorOff("move_door closed exception")
            print(e)
    else:
        print("That's not a state newman.")
        #MotorOff()

        
    print("Door move complete! Door is now %s" % desired_state)
    if desired_state == "Open":
        # Turn the handler back on now that door moving is complete.
        Limit_Switch_Open.irq(handler=Door_Closed_Handler)
        LS_door_closed_state = Limit_Switch_Closed.value()
        set_neopixel_color("blue")
        time.sleep(2)
        set_neopixel_color("green")
    else:
        # Turn the handler back on now that door moving is complete.
        Limit_Switch_Closed.irq(handler=Door_Open_Handler)
        LS_door_open_state = Limit_Switch_Open.value()
        set_neopixel_color("blue")
        time.sleep(2)
        set_neopixel_color("red")
        
    #Update the door state on MQTT
    client.publish("from_the_door", desired_state)

# Set MQTT callbacks
client.set_callback(on_message)

# Connect to MQTT broker
client.connect()
client.subscribe(MQTT_TOPIC_REQUEST)


# Main loop
try:
    while True:
        # Check for new MQTT messages
        client.check_msg()
        time.sleep(1)
        
finally:
    client.disconnect()


