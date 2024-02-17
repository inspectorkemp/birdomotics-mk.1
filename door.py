from umqtt.simple import MQTTClient
import time
import network
import neopixel
from machine import Pin, Timer

# Define WiFi and MQTT details
WIFI_SSID = ""
WIFI_PASS = ""
MQTT_BROKER = ""
MQTT_USERNAME = "mqtt"
MQTT_PASSWORD = ""
MQTT_TOPIC_REQUEST = b"chicken_door_state"

# NeoPixel configuration
num_pixels = 1  # Number of NeoPixels
neo_pin = 13    # Pin connected to the NeoPixel
np = neopixel.NeoPixel(machine.Pin(neo_pin), num_pixels)

# Define Relay configurations for limit switches
# Relay_Open_Pin = 14
# Limit_Switch_Open = Pin(Limit_Switch_Open_Pin, Pin.IN)
Limit_Switch_Closed_Pin = 0
Limit_Switch_Closed = Pin(Limit_Switch_Closed_Pin, Pin.IN)

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

# Door Limit Switch State Variables
LS_door_closed_state = ""

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
    print("Door closed limit switch was triggered!")

# Create Closed Relay Handler
Limit_Switch_Closed.irq(trigger=machine.Pin.IRQ_RISING, handler = Door_Closed_Handler)

def MotorOff():
    Relay_A.value(0)
    Relay_B.value(0)

# MQTT Message Received
def on_message(topic, msg):
    print("Topic updated - doing work!")
    set_neopixel_color("blue")
    global current_door_state
    
    #Decode the desired state from MQTT Topic:
    new_desired_state = msg.decode("utf-8")
    print("New Desired State Message Received %s" % new_desired_state)
    
    # Some logic to flip the current door state until limit switches can be polled
    if new_desired_state == "Closed":
        current_door_state = "Open"
    else:
        current_door_state = "Closed"
    
    # Check if door is in the desired state already - if yes, don't do anything.
    # Check limit switches here
    if new_desired_state == current_door_state:
        print("Door is already in desired state %s" % current_door_state)
        if current_door_state == "Closed":
            set_neopixel_color("red")
        else:
            set_neopixel_color("green")
    else:
        # Door is not in desired state, moving...
        move_door(new_desired_state)
    
def move_door(desired_state):
    global LS_door_closed_state
    #Arbitrary counter until limit switch logic is added
    polling_counter = 0

    # Relay gets flipped here - motor turning
    print("Door is moving to state: %s" % desired_state)
    if desired_state == "Open":
        print("Motor on: opening")
        time.sleep(5)
        set_neopixel_color("green")
        Relay_A.value(1)
        Relay_B.value(0)
    elif desired_state == "Closed":
        print("Motor on: closing")
        time.sleep(5)
        LS_door_closed_state = 0
        Relay_A.value(0)
        Relay_B.value(1)
        set_neopixel_color("red")
    else:
        print("That's not a state newman.")
        MotorOff()
    #Wait for door to finish
    try:
        while LS_door_closed_state == 0:    
            print("polling the fake limit switches until door is done moving...")
            polling_counter = polling_counter + 1
            # print("Polling counter value: %i" % polling_counter)
            time.sleep(3)
    except Exception as e:
        print(e)
        
    print("Door move complete! Door is now %s" % desired_state)
    if desired_state == "Open":
        set_neopixel_color("blue")
        time.sleep(2)
        set_neopixel_color("green")
    else:
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

