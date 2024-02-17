from umqtt.simple import MQTTClient
import time
import network
import neopixel
import machine
import ujson as json  # Using ujson for JSON parsing, ensure it's installed

Define WiFi and MQTT details
WIFISSID = "YourWiFiSSID"
WIFI_PASS = "YourWiFiPassword"
MQTT_BROKER = "YourMQTTBrokerAddress"
MQTT_USERNAME = "mqtt"
MQTT_PASSWORD = "mqtt"
MQTT_TOPIC_REQUEST = b"chicken_door_state"

NeoPixel configuration
NUM_PIXELS = 1  # Number of NeoPixels
NEO_PIN = 13    # Pin connected to the NeoPixel
np = neopixel.NeoPixel(machine.Pin(NEO_PIN), NUM_PIXELS)

NeoPixel colors
NEOPIXEL_RED = (255, 0, 0)
NEOPIXEL_GREEN = (0, 255, 0)
NEOPIXEL_BLUE = (0, 0, 255)

Limit switch simulation
LIMIT_SWITCH_POLL_COUNT = 3
LIMIT_SWITCH_POLL_INTERVAL = 2  # in seconds

Variables to track the current door state and desired door state
current_door_state = ""

Initialize WiFi
def connect_wifi(ssid, password):
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(ssid, password)
    while not wifi.isconnected():
        time.sleep(1)
    return wifi

Initialize MQTT client
def connect_mqtt(broker, username, password):
    client = MQTTClient("micropython_client", broker, user=username, password=password)
    client.connect()
    return client

Function to set NeoPixel color
def set_neopixel_color(color):
    colors = {"red": NEOPIXEL_RED, "green": NEOPIXEL_GREEN, "blue": NEOPIXEL_BLUE}
    np[0] = colors.get(color, NEOPIXEL_BLUE)
    np.write()

MQTT Message Received
def on_message(topic, msg):
    print("Topic updated - doing work!")
    set_neopixel_color("blue")
    global current_door_state

Decode the desired state from MQTT Topic
    new_desired_state = msg.decode("utf-8")
    print("New Desired State Message Received:", new_desired_state)

Some logic to flip the current door state until limit switches can be polled
    current_door_state = "Open" if new_desired_state == "Closed" else "Closed"

Check if door is in the desired state already
    if new_desired_state == current_door_state:
        print("Door is already in the desired state:", current_door_state)
        set_neopixel_color("red" if current_door_state == "Closed" else "green")
    else:
        # Door is not in desired state, moving...
        move_door(new_desired_state)

Move the door
def move_door(desired_state):
    print("Door is moving to state:", desired_state)
    set_neopixel_color("green" if desired_state == "Open" else "red")

Simulate waiting for door to finish
    for  in range(LIMITSWITCHPOLLCOUNT):
        print("Polling the fake limit switches until door is done moving...")
        time.sleep(LIMITSWITCH_POLL_INTERVAL)

    print("Door move complete! Door is now", desired_state)
    set_neopixel_color("green" if desired_state == "Open" else "red")
    time.sleep(2)
    set_neopixel_color("blue")


# Update the door state on MQTT
client.publish(MQTT_TOPIC_REQUEST, desired_state)
def main():
    wifi = connect_wifi(WIFI_SSID, WIFI_PASS)
    client = connect_mqtt(MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD)

    # Set MQTT callbacks
    client.set_callback(on_message)
    client.subscribe(MQTT_TOPIC_REQUEST)

    # Main loop
    try:
        while True:
            # Check for new MQTT messages
            client.check_msg()

    finally:
        client.disconnect()

if __name == "__main":
    main()