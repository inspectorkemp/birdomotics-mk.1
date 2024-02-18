from umqtt.simple import MQTTClient
import time
import network
import neopixel
from machine import Pin

# Configuration Constants
WIFI_SSID = ""
WIFI_PASS = ""
MQTT_BROKER = ""
MQTT_USERNAME = "mqtt"
MQTT_PASSWORD = ""
MQTT_TOPIC_REQUEST = b"chicken_door_state"

# NeoPixel Configuration
NUM_PIXELS = 1  # Number of NeoPixels
NEO_PIN = 13    # Pin connected to the NeoPixel
NEO_RED = (255, 0, 0)
NEO_GREEN = (0, 255, 0)
NEO_BLUE = (0, 0, 255)

# Door Configuration
LIMIT_SWITCH_CLOSED_PIN = 0
RELAY_A_PIN = 14
RELAY_B_PIN = 15

# Initialize NeoPixel
np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_PIXELS)

# Initialize WiFi
def connect_to_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASS)
    
    while not wifi.isconnected():
        time.sleep(1)

# Initialize MQTT client
def connect_to_mqtt():
    client = MQTTClient("micropython_client", MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(MQTT_TOPIC_REQUEST)
    return client

# NeoPixel Color Setter
def set_neopixel_color(color):
    color_map = {"red": NEO_RED, "green": NEO_GREEN, "blue": NEO_BLUE}
    np[0] = color_map.get(color, NEO_BLUE)
    np.write()

# Motor Off Function
def motor_off(relay_a, relay_b):
    relay_a.value(0)
    relay_b.value(0)

# MQTT Message Received Callback
def on_message(topic, msg):
    print("Topic updated - doing work!")
    set_neopixel_color("blue")
    global current_door_state
    
    new_desired_state = msg.decode("utf-8")
    print("New Desired State Message Received %s" % new_desired_state)
    
    if new_desired_state == "Closed":
        current_door_state = "Open"
    else:
        current_door_state = "Closed"
    
    if new_desired_state == current_door_state:
        print("Door is already in desired state %s" % current_door_state)
        set_neopixel_color("red" if current_door_state == "Closed" else "green")
    else:
        move_door(new_desired_state)

# Door Movement Function
def move_door(desired_state, relay_a, relay_b, limit_switch_closed_pin):
    polling_counter = 0

    print("Door is moving to state: %s" % desired_state)
    set_neopixel_color("green" if desired_state == "Open" else "red")
    
    if desired_state == "Open":
        print("Motor on: opening")
        time.sleep(5)
        relay_a.value(1)
        relay_b.value(0)
    elif desired_state == "Closed":
        print("Motor on: closing")
        time.sleep(5)
        limit_switch_closed_state = 0
        relay_a.value(0)
        relay_b.value(1)
        set_neopixel_color("red")
    else:
        print("Invalid state.")
        motor_off(relay_a, relay_b)

    try:
        while limit_switch_closed_state == 0:    
            print("Polling the limit switches until door is done moving...")
            polling_counter += 1
            time.sleep(3)
    except Exception as e:
        print(e)
        
    print("Door move complete! Door is now %s" % desired_state)
    set_neopixel_color("blue")
    time.sleep(2)
    set_neopixel_color("green" if desired_state == "Open" else "red")

# Main Function
def main():
    connect_to_wifi()
    client = connect_to_mqtt()

    # Initialize relay pins
    relay_a = Pin(RELAY_A_PIN, Pin.OUT)
    relay_b = Pin(RELAY_B_PIN, Pin.OUT)

    # Initialize limit switch interrupt handler
    limit_switch_closed_state = 1
    limit_switch_closed = Pin(LIMIT_SWITCH_CLOSED_PIN, Pin.IN)
    limit_switch_closed.irq(trigger=Pin.IRQ_RISING, handler=lambda p: on_limit_switch_closed(limit_switch_closed_state))

    try:
        while True:
            motor_off(relay_a, relay_b)
            client.check_msg()
            time.sleep(1)
        
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
