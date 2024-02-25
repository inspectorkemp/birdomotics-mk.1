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
NUM_PIXELS = 1  # Number of NeoPixels
NEO_PIN = 13    # Pin connected to the NeoPixel
NP = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_PIXELS)

# Define Relay configurations for limit switches
LIMIT_SWITCH_CLOSED_PIN = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
LIMIT_SWITCH_OPEN_PIN = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_UP)

# Motor assignments
RELAY_A_PIN = 14
RELAY_B_PIN = 15
RELAY_A = machine.Pin(RELAY_A_PIN, machine.Pin.OUT)
RELAY_B = machine.Pin(RELAY_B_PIN, machine.Pin.OUT)

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
def door_closed_handler(pin):
    global LS_door_closed_state
    LS_door_closed_state = 1
    motor_off()
    print("Door closed limit switch was triggered!")

# DoorOpen.py
def door_open_handler(pin):
    global LS_door_open_state
    LS_door_open_state = 1
    motor_off()
    print("Door open limit switch was triggered!")

# Create Closed Limit Switch Handler
LIMIT_SWITCH_CLOSED_PIN.irq(trigger=machine.Pin.IRQ_FALLING, handler=door_closed_handler)

# Create Open Limit Switch Handler
LIMIT_SWITCH_OPEN_PIN.irq(trigger=machine.Pin.IRQ_FALLING, handler=door_open_handler)

# Function to set NeoPixel color
def set_neopixel_color(color):
    neopixel_red = (255, 0, 0)
    neopixel_green = (0, 255, 0)
    neopixel_blue = (0, 0, 255)
    if color == "red":
        NP[0] = neopixel_red
    elif color == "green":
        NP[0] = neopixel_green
    elif color == "blue":
        NP[0] = neopixel_blue
    NP.write()

def motor_off():
    RELAY_A.value(0)
    RELAY_B.value(0)

# MQTT Message Received
def on_message(topic, msg):
    print("Topic updated - doing work!")
    set_neopixel_color("blue")
    global current_door_state
    # stubbed in for testing purposes until open limit switch is connected

    # Decode the desired state from MQTT Topic:
    new_desired_state = msg.decode("utf-8")
    print("New Desired State Message Received %s" % new_desired_state)

    # Check limit switches for door state
    if LIMIT_SWITCH_CLOSED_PIN.value() == 1 and LIMIT_SWITCH_OPEN_PIN.value() == 0:
        print("Limit switches polled - door is currently Closed")
        current_door_state = "Closed"
    elif LIMIT_SWITCH_OPEN_PIN.value() == 1 and LIMIT_SWITCH_CLOSED_PIN.value() == 0:
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
    print("Checking LS_door_closed_state == %i" % LS_door_closed_state)
    print("Checking LS_door_open_sate == %i" % LS_door_open_state)
    if desired_state == "Open":
        print("Motor on: opening")
        time.sleep(5)
        set_neopixel_color("green")
        RELAY_A.value(1)
        RELAY_B.value(0)
        # Wait for door to finish
        try:
            while LS_door_open_state == 0:
                print("Waiting for interrupt request from door open limit switch...")
                time.sleep(3)
        except Exception as e:
            motor_off()
            print(f"Error during door open: {e}")
    elif desired_state == "Closed":
        print("Motor on: closing")
        time.sleep(5)
        RELAY_A.value(0)
        RELAY_B.value(1)
        set_neopixel_color("red")
        # Wait for door to finish
        try:
            while LS_door_closed_state == 0:
                print("Waiting for interrupt request from door closed limit switch...")
                time.sleep(3)
        except Exception as e:
            motor_off()
            print(f"Error during door close: {e}")
    else:
        print("Invalid state.")
        motor_off()

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

# Set MQTT callbacks
client.set_callback(on_message)

# Connect to MQTT broker
client.connect()
client.subscribe(MQTT_TOPIC_REQUEST)

# Main loop
try:
    while True:
        # Turn Relays for Motor Off
        motor_off()
        # Check for new MQTT messages
        client.check_msg()
        time.sleep(1)

finally:
    client.disconnect()
