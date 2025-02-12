from umqtt.simple import MQTTClient
import time
import network
import neopixel
import secrets
from machine import Pin, Timer, I2C
from ssd1306 import SSD1306_I2C
from enum import Enum, unique

# Constants and Configuration
@unique
class DoorState(Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    UNKNOWN = "Unknown"
    MOVING = "Moving"

WIFI_SSID = secrets.WIFI_SSID
WIFI_PASS = secrets.WIFI_PASS
MQTT_BROKER = secrets.MQTT_BROKER
MQTT_USERNAME = secrets.MQTT_USERNAME
MQTT_PASSWORD = secrets.MQTT_PASSWORD
MQTT_TOPIC_REQUEST = secrets.MQTT_TOPIC_REQUEST
MQTT_TOPIC_STATE = "from_the_door"
MQTT_TOPIC_ERROR = "door_error"

# NeoPixel configuration
NUM_PIXELS = 1
NEO_PIN = 13
np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_PIXELS)

# Pin assignments
LIMIT_SWITCH_CLOSED_PIN = 0
LIMIT_SWITCH_OPEN_PIN = 1
RELAY_A_PIN = 14
RELAY_B_PIN = 15

# SSD1306 OLED display configuration
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C = I2C(0, scl=Pin(22), sda=Pin(21))  # Adjust pins based on your hardware
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, OLED_I2C)

# Initialize pins
Limit_Switch_Closed = Pin(LIMIT_SWITCH_CLOSED_PIN, Pin.IN, Pin.PULL_UP)
Limit_Switch_Open = Pin(LIMIT_SWITCH_OPEN_PIN, Pin.IN, Pin.PULL_UP)
Relay_A = Pin(RELAY_A_PIN, Pin.OUT)
Relay_B = Pin(RELAY_B_PIN, Pin.OUT)

# Global variables
current_door_state = DoorState.UNKNOWN
motor_timeout = 30  # Timeout for motor operation in seconds

# Logging function
def log(message):
    print(f"[LOG] {message}")
    update_display(f"LOG: {message}")

# Update SSD1306 display
def update_display(message, line=None):
    oled.fill(0)  # Clear the display
    if line is not None:
        oled.text(message, 0, line * 10)
    else:
        oled.text(message, 0, 0)
    oled.show()

# NeoPixel control
def set_neopixel_color(color):
    colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "off": (0, 0, 0)
    }
    np[0] = colors.get(color, (0, 0, 0))
    np.write()

# Motor control
def motor_off():
    Relay_A.value(0)
    Relay_B.value(0)
    log("Motor turned off.")

def motor_on(direction):
    if direction == "open":
        Relay_A.value(1)
        Relay_B.value(0)
    elif direction == "close":
        Relay_A.value(0)
        Relay_B.value(1)
    log(f"Motor turned on to {direction} the door.")

# Door state management
def update_door_state():
    global current_door_state
    if Limit_Switch_Closed.value() == 0 and Limit_Switch_Open.value() == 1:
        current_door_state = DoorState.CLOSED
    elif Limit_Switch_Closed.value() == 1 and Limit_Switch_Open.value() == 0:
        current_door_state = DoorState.OPEN
    else:
        current_door_state = DoorState.UNKNOWN
    log(f"Door state updated to: {current_door_state.value}")
    update_display(f"State: {current_door_state.value}", line=0)

# MQTT message handler
def on_message(topic, msg):
    global current_door_state
    set_neopixel_color("blue")
    message = msg.decode("utf-8").lower()
    log(f"Received MQTT message: {message}")

    update_door_state()

    if message == "door_check":
        client.publish(MQTT_TOPIC_STATE, current_door_state.value)
    elif message in ["open", "close"] and current_door_state.value.lower() != message:
        move_door(message)
    else:
        log(f"No action taken. Door is already {current_door_state.value}.")

# Door movement logic
def move_door(direction):
    global current_door_state
    current_door_state = DoorState.MOVING
    log(f"Starting to {direction} the door.")
    update_display(f"Moving: {direction}", line=1)

    motor_on(direction)
    start_time = time.time()
    target_switch = Limit_Switch_Open if direction == "open" else Limit_Switch_Closed

    try:
        while target_switch.value() == 0:
            if time.time() - start_time > motor_timeout:
                raise Exception("Motor timeout: Door movement took too long.")
            time.sleep(0.1)
    except Exception as e:
        log(f"Error: {e}")
        client.publish(MQTT_TOPIC_ERROR, str(e))
        update_display(f"Error: {e}", line=2)
    finally:
        motor_off()
        update_door_state()
        client.publish(MQTT_TOPIC_STATE, current_door_state.value)
        set_neopixel_color("green" if current_door_state == DoorState.OPEN else "red")

# WiFi connection
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASS)
    while not wifi.isconnected():
        log("Connecting to WiFi...")
        time.sleep(1)
    log("WiFi connected.")
    update_display("WiFi: Connected", line=3)

# MQTT connection
def connect_mqtt():
    global client
    client = MQTTClient("micropython_client", MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(MQTT_TOPIC_REQUEST)
    log("MQTT connected.")
    update_display("MQTT: Connected", line=4)

# Main loop
def main():
    connect_wifi()
    connect_mqtt()
    update_door_state()

    try:
        while True:
            client.check_msg()
            time.sleep(1)
    except Exception as e:
        log(f"Fatal error: {e}")
        update_display(f"Fatal: {e}", line=5)
    finally:
        client.disconnect()
        log("MQTT disconnected.")
        update_display("MQTT: Disconnected", line=5)

if __name__ == "__main__":
    main()
