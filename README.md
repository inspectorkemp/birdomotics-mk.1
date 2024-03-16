# birdomotics-mk.1
To-Do list: in somewhat priority order

~~Troubleshoot issue where door open routine is not clearly caught.~~

~~Publish MQTT messages during and post door state changes.~~

(BN) Create .yaml files for Home Assistant integration.

(MF) Configure a way to query door position switches *only* via MQTT subscribe and then publish the results.


## Requirements
Create secrets.py, define secrets, then import: `import secrets`
Insert the following into the secrets.py, supplying the values inside the double quotes:
```
# Define WiFi and MQTT details
WIFI_SSID = ""
WIFI_PASS = ""
MQTT_BROKER = ""
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
MQTT_TOPIC_REQUEST = ""
```

# MQTT
## Topics
- `chicken_door_state` - Accepts three input values to either move the door or check the current state fo the door:
    1. Open - open the door
    2. Closed - close the door
    3. door_check - poll the limit switches to determine the state of the door then publish the state to the `from_the_door` topic.
- `from_the_door` - topic that the pico publishes the state of the door when it is finished moving or the current state of the door when publishing a `door_check` value to the `chicken_door_state` topic.
