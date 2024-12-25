from umqtt.simple import MQTTClient
import time
import network
import neopixel
import secrets
from machine import Pin, Timer

# WiFi and MQTT details from secrets module
WIFI_SSID = secrets.WIFI_SSID
WIFI_PASS = secrets.WIFI_PASS
MQTT_BROKER = secrets.MQTT_BROKER
MQTT_USERNAME = secrets.MQTT_USERNAME
MQTT_PASSWORD = secrets.MQTT_PASSWORD
MQTT_TOPIC_REQUEST = secrets.MQTT_TOPIC_REQUEST
MQTT_TOPIC_STATE = "from_the_door"  # Topic to receive door state

# NeoPixel configuration
NEO_PIXEL_PIN = 13  # Pin connected to the NeoPixel
NUM_PIXELS = 1      # Number of NeoPixels
np = neopixel.NeoPixel(Pin(NEO_PIXEL_PIN), NUM_PIXELS)

# Button configuration
BUTTON_OPEN_PIN = 14  # Pin for "Open" button
BUTTON_CLOSE_PIN = 15  # Pin for "Close" button
button_open = Pin(BUTTON_OPEN_PIN, Pin.IN, Pin.PULL_UP)
button_close = Pin(BUTTON_CLOSE_PIN, Pin.IN, Pin.PULL_UP)

# Function to set NeoPixel color
def set_neopixel_color(color):
    if color == "green":
        np[0] = (0, 255, 0)  # Green
    elif color == "blue":
        np[0] = (0, 0, 255)  # Blue
    else:
        np[0] = (0, 0, 0)    # Off
    np.write()

# Connect to WiFi
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASS)
    print("Connecting to WiFi...")
    while not wifi.isconnected():
        time.sleep(1)
    print("Connected to WiFi:", wifi.ifconfig())

# MQTT message callback
def on_message(topic, msg):
    print("Received message on topic {}: {}".format(topic, msg))
    if msg == b"Open":
        set_neopixel_color("green")
    elif msg == b"Closed":
        set_neopixel_color("blue")
    else:
        set_neopixel_color("off")

# Button press interrupt callbacks
def open_button_pressed(pin):
    print("Open button pressed!")
    client.publish(MQTT_TOPIC_REQUEST, "Open")

def close_button_pressed(pin):
    print("Close button pressed!")
    client.publish(MQTT_TOPIC_REQUEST, "Closed")

# Main function
def main():
    global client

    # Connect to WiFi
    connect_wifi()

    # Initialize MQTT client
    client = MQTTClient("pico_status", MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(MQTT_TOPIC_STATE)
    print("Connected to MQTT broker and subscribed to", MQTT_TOPIC_STATE)

    # Attach button interrupts
    button_open.irq(trigger=Pin.IRQ_FALLING, handler=open_button_pressed)
    button_close.irq(trigger=Pin.IRQ_FALLING, handler=close_button_pressed)

    # Default NeoPixel state
    set_neopixel_color("blue")  # Assume door is closed initially

    # Main loop to process MQTT messages
    try:
        while True:
            client.check_msg()
            time.sleep(1)
    finally:
        client.disconnect()
        set_neopixel_color("off")  # Turn off NeoPixel on exit

# Run the main function
if __name__ == "__main__":
    main()
