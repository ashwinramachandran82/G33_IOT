#!/usr/bin/env python
# Members - Ashwin Ramachandran & Norman Cho
# Project code - G33
# Purpose - To read and send the Oxygen levels to the AWS IoT Cloud and receive actuation commands from the AWS IoT cloud to activate the buzzer when the oxygen level drops below 400

import time
import datetime
import ssl
import json
import paho.mqtt.client as mqtt
import grovepi

# TODO: Name of our Raspberry Pi, also known as our "Thing Name"
deviceName = "g33_pi"
# TODO: Public certificate of our Raspberry Pi, as provided by AWS IoT.
deviceCertificate = "ace9fccbc5-certificate.pem.crt"
# TODO: Private key of our Raspberry Pi, as provided by AWS IoT.
devicePrivateKey = "ace9fccbc5-private.pem.key"
# Root certificate to authenticate AWS IoT when we connect to their server.
awsCert = "aws-iot-rootCA.crt"
isConnected = False


# O2 gas sensor connected to Port A0 in grove shield board
# Buzzer connected to Port D8 in grove shield board

gas_sensor_port = 0
buzzer = 8



# This is the main logic of the program.  We connect to AWS IoT via MQTT, send sensor data periodically to AWS IoT,
# and handle any actuation commands received from AWS IoT.
def main():
    global isConnected
    # Create an MQTT client for connecting to AWS IoT via MQTT.
    client = mqtt.Client(deviceName + "_sr")  # Client ID must be unique because AWS will disconnect any duplicates.
    client.on_connect = on_connect  # When connected, call on_connect.
    client.on_message = on_message  # When message received, call on_message.
    client.on_log = on_log  # When logging debug messages, call on_log.

    # Set the certificates and private key for connecting to AWS IoT.  TLS 1.2 is mandatory for AWS IoT and is supported
    # only in Python 3.4 and later, compiled with OpenSSL 1.0.1 and later.
    client.tls_set(awsCert, deviceCertificate, devicePrivateKey, ssl.CERT_REQUIRED, ssl.PROTOCOL_TLSv1_2)

    # Connect to AWS IoT server.  Use AWS command line "aws iot describe-endpoint" to get the address.
    print("Connecting to AWS IoT...")
    client.connect("A1P01IYM2DOZA0.iot.us-west-2.amazonaws.com", 8883, 60)

    # Start a background thread to process the MQTT network commands concurrently, including auto-reconnection.
    client.loop_start()

    # Configure the Grove buzzer port for output.
    grovepi.pinMode(buzzer, "OUTPUT")
    time.sleep(1)

    # Loop forever.
    while True:
        try:
            # If we are not connected yet to AWS IoT, wait 1 second and try again.
            if not isConnected:
                time.sleep(1)
                continue

            # Read O2 Sensor values. Prepare our sensor data in JSON format.
            payload = {
                "state": {
                    "reported": {

                        "oxygenlevel": grovepi.analogRead(gas_sensor_port),
                        "timestamp": datetime.datetime.now().isoformat()

                    }
                }
            }
            print("Sending sensor data to AWS IoT...\n" +
                  json.dumps(payload, indent=4, separators=(',', ': ')))

            # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
            client.publish("$aws/things/" + deviceName + "/shadow/update", json.dumps(payload))
            print("Sent to AWS IoT")

            # Wait 30 seconds before sending the next set of sensor data.
            time.sleep(30)

        except KeyboardInterrupt:
            break
        except IOError:
            print("Error")


# This is called when we are connected to AWS IoT via MQTT.
# We subscribe for notifications of desired state updates.
def on_connect(client, userdata, flags, rc):
    global isConnected
    isConnected = True
    print("Connected to AWS IoT")
    # Subscribe to our MQTT topic so that we will receive notifications of updates.
    topic = "$aws/things/" + deviceName + "/shadow/update/accepted"
    print("Subscribing to MQTT topic " + topic)
    client.subscribe(topic)


# This is called when we receive a subscription notification from AWS IoT.
# If this is an actuation command, we execute it.
def on_message(client, userdata, msg):
    # Convert the JSON payload to a Python dictionary.
    # The payload is in binary format so we need to decode as UTF-8.
    payload2 = json.loads(msg.payload.decode("utf-8"))
    print("Received message, topic: " + msg.topic + ", payload:\n" +
          json.dumps(payload2, indent=4, separators=(',', ': ')))

    # If there is a desired state in this message, then we actuate
    if payload2.get("state") is not None and payload2["state"].get("desired") is not None:
        # Get the desired state and loop through all attributes inside.
        desired_state = payload2["state"]["desired"]
        for attribute in desired_state:
            # We handle the attribute and desired value by actuating.
            value = desired_state.get(attribute)
            actuate(client, attribute, value)


# Control my actuators based on the specified attribute and value e.g. "buzzerstate=on" will switch on the buzzer
def actuate(client, attribute, value):
    if attribute == "timestamp":
        # Ignore the timestamp attribute, it's only for info.
        return
    print("Setting " + attribute + " to " + value + "...")
    if attribute == "buzzerstate":
        # We actuate the Buzzer for "on" and "off"
        if value == "on":
            # Switch on LED.
            grovepi.digitalWrite(buzzer, 1)
            send_reported_state(client, "buzzerstate", "on")
            time.sleep(20)
            grovepi.digitalWrite(buzzer, 0)
            send_reported_state(client, "buzzerstate", "off")
            return

    # Show an error if attribute or value are incorrect.
    print("Error: Don't know how to set " + attribute + " to " + value)


# Send the reported state of our actuator tp AWS IoT after it has been triggered, e.g. "buzzerstate=on"
def send_reported_state(client, attribute, value):
    # Prepare our sensor data in JSON format.
    payload = {
        "state": {
            "reported": {
                attribute: value,
                "timestamp": datetime.datetime.now().isoformat()
            }
        }
    }
    print("Sending sensor data to AWS IoT...\n" +
          json.dumps(payload, indent=4, separators=(',', ': ')))

    # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
    client.publish("$aws/things/" + deviceName + "/shadow/update", json.dumps(payload))
    print("Sent to AWS IoT")


# Print out log messages for tracing.
def on_log(client, userdata, level, buf):
    print("Log: " + buf)


# Start the main program.
main()
