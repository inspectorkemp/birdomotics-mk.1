from machine import Pin, Timer
from umqtt.simple import MQTTClient
import neopixel
import time
import network
import secrets

# WiFi and MQTT Configuration
WIFI_SSID = secrets.WIFI_SSID
WIFI_PASS = secrets.WIFI_PASS
MQTT_BROKER = secrets.MQTT_BROKER
MQTT_USERNAME = secrets.MQTT_USERNAME
MQTT_PASSWORD = secrets.MQTT_PASSWORD
MQTT_TOPIC_REQUEST = secrets.MQTT_TOPIC_REQUEST
MQTT_TOPIC_STATUS = "from_the_door"

# NeoPixel Configuration
NUM_PIXELS = 2  # Two NeoPixels
NEO_PIN = 13    # Pin connected to the NeoPixels
np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_PIXELS)

# Button Configuration
BUTTON_OPEN_PIN = 0  # Pin for "Open" button
BUTTON_CLOSE_PIN = 1  # Pin for "Close" button
button_open = Pin(BUTTON_OPEN_PIN, Pin.IN, Pin.PULL_UP)
button_close = Pin(BUTTON_CLOSE_PIN, Pin.IN, Pin.PULL_UP)

# Global Variables
current_status = "Unknown"  # Tracks the current door status
is_in_motion = False         # Tracks if the door is in motion

def set_neopixel_colors(motion, status):
    """Sets NeoPixel colors based on door motion and status."""
    # Motion NeoPixel
    if motion:
        np[0] = (255, 255, 0)  # Yellow indicates motion
    else:
        np[0] = (0, 0, 0)  # Off when not in motion

    # Status NeoPixel
    if status == "Open":
        np[1] = (0, 255, 0)  # Green for open
    elif status == "Closed":
        np[1] = (255, 0, 0)  # Red for closed
    else:
        np[1] = (0, 0, 255)  # Blue for unknown

    np.write()

# WiFi Connection
def connect_to_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASS)
    print("Connecting to WiFi...")
    while not wifi.isconnected():
        time.sleep(1)
    print("Connected to WiFi:", wifi.ifconfig())

# MQTT Callbacks
def on_message(topic, msg):
    global current_status, is_in_motion

    # Update status based on received message
    status = msg.decode("utf-8")
    print("Received MQTT message:", status)

    if status in ["Open", "Closed"]:
        is_in_motion = False
        current_status = status
    elif status == "Moving":
        is_in_motion = True
    else:
        current_status = "Unknown"

    set_neopixel_colors(is_in_motion, current_status)

# Button Handlers
def handle_open_request(pin):
    print("Open button pressed")
    client.publish(MQTT_TOPIC_REQUEST, "Open")

def handle_close_request(pin):
    print("Close button pressed")
    client.publish(MQTT_TOPIC_REQUEST, "Closed")

# Main Program
connect_to_wifi()

# Initialize MQTT Client
client = MQTTClient("pico_display_client", MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)
client.set_callback(on_message)
client.connect()
client.subscribe(MQTT_TOPIC_STATUS)

# Configure Buttons with Interrupts
button_open.irq(trigger=Pin.IRQ_FALLING, handler=handle_open_request)
button_close.irq(trigger=Pin.IRQ_FALLING, handler=handle_close_request)

# Main Loop
try:
    print("Monitoring door status...")
    while True:
        client.check_msg()  # Check for new MQTT messages
        time.sleep(0.1)     # Small delay to avoid excessive polling

finally:
    client.disconnect()
    print("Disconnected from MQTT broker.")
