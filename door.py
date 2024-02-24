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
# Relay_Open_Pin = 14
# Limit_Switch_Open = Pin(Limit_Switch_Open_Pin, Pin.IN)
Limit_Switch_Closed_Pin = 0
Limit_Switch_Closed = Pin(Limit_Switch_Closed_Pin, Pin.IN, machine.Pin.PULL_UP)
# Limit_Switch_Open = False
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

# Door Limit Switch State Variables - start at 0 until polled on message change
LS_door_closed_state = 0
LS_door_open_state = 0

# Initialize WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

# Wait for the WiFi connection to be established
while not wifi.isconnected():
    time.sleep(1)

# Initialize MQTT client
client = MQTTClient("micropython_client", MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)

# DoorClosing.py
def Door_Closed_Handler(self):
    global LS_door_closed_state
    LS_door_closed_state = 1
    MotorOff()
    print("Door closed limit switch value is -- %i" % LS_door_closed_state)
    print("Door closed limit switch was triggered!")
    
#DoorOpen.py
def Door_Open_Handler(self):
    global LS_door_open_state
    LS_door_open_state = 1
    MotorOff()
    print("Door open limit switch value is -- %i" % LS_door_open_state)
    print("Door open limit switch was triggered!")

# Create Closed Limit Switch Handler
Limit_Switch_Closed.irq(trigger=machine.Pin.IRQ_FALLING, handler = Door_Closed_Handler)

# Create Open Limit Switch Handler
Limit_Switch_Open.irq(trigger=machine.Pin.IRQ_FALLING, handler = Door_Open_Handler)

def MotorOff():
    Relay_A.value(0)
    Relay_B.value(0)

# MQTT Message Received
def on_message(topic, msg):
    print("Topic updated - doing work!")
    set_neopixel_color("blue")
    global current_door_state
    #stubbed in for testing purposes until open limit switch is connected
        
    #Decode the desired state from MQTT Topic:
    new_desired_state = msg.decode("utf-8")
    print("New Desired State Message Received %s" % new_desired_state)
    
    # Check limit switches for door state 
    if Limit_Switch_Closed.value() == False:
        print("Limit switches polled - door is currently Closed")
        current_door_state = "Closed"
    elif Limit_Switch_Open.value() == False:
        current_door_state = "Open"
        print("Limit switches polled - door is currently Open")
    
    # Check if door is in the desired state already - if yes, don't do anything.
    if new_desired_state == current_door_state:
        print("Door is already in desired state %s" % current_door_state)
        if current_door_state == "Closed":
            set_neopixel_color("red")
        elif current_door_state == "Open":
            set_neopixel_color("green")
    else:
        # Door is not in desired state, moving...
        move_door(new_desired_state)
    
def move_door(desired_state):
    global LS_door_closed_state
    global LS_door_open_state

    # Relay gets flipped here - motor turning
    print("Door is moving to state: %s" % desired_state)
    if desired_state == "Open":
        print("Motor on: opening")
        time.sleep(5)
        set_neopixel_color("green")
        Relay_A.value(1)
        Relay_B.value(0)
        #Wait for door to finish
        try:
            while LS_door_open_state == 0:    
                print("Waiting for interrupt request from door open limit switch...")
                time.sleep(3)
        except Exception as e:
            MotorOff()
            print(e)
    elif desired_state == "Closed":
        print("Motor on: closing")
        time.sleep(5)
        Relay_A.value(0)
        Relay_B.value(1)
        set_neopixel_color("red")
        #Wait for door to finish
        try:
            while LS_door_closed_state == 0:    
                print("Waiting for interrupt request from door closed limit switch...")
                time.sleep(3)
        except Exception as e:
            MotorOff()
            print(e)
    else:
        print("That's not a state newman.")
        MotorOff()

        
    print("Door move complete! Door is now %s" % desired_state)
    if desired_state == "Open":
        LS_door_closed_state = 0
        set_neopixel_color("blue")
        time.sleep(2)
        set_neopixel_color("green")
    else:
        LS_door_open_state = 0
        set_neopixel_color("blue")
        time.sleep(2)
        set_neopixel_color("red")
        
    #Update the door state on MQTT
    # client.publish(MQTT_TOPIC_REQUEST, desired_state)

# Set MQTT callbacks
client.set_callback(on_message)

# Connect to MQTT broker
client.connect()
client.subscribe(MQTT_TOPIC_REQUEST)


# Main loop
try:
    while True:
        # Turn Relays for Motor Off
        MotorOff()
        # Check for new MQTT messages
        client.check_msg()
        time.sleep(1)
        
finally:
    client.disconnect()

