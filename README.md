# birdomotics-mk.1
To-Do list: in somewhat priority order

Troubleshoot issue where door open routine is not clearly caught.

Publish MQTT messages during and post door state changes.

Create .yaml files for Home Assistant integration.

Configure a way to query door position switches *only* via MQTT subscribe and then publish the results.


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
