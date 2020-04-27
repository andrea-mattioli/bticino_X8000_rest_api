import os
import sys
import subprocess
import logging
import paho.mqtt.client as paho   # pip install paho-mqtt
import time
import socket
import string
import yaml
from bticino import send_thermostat_cmd, load_api_config_arg

qos=2
mqtt_config_file = 'config/mqtt_config.yml'
with open(mqtt_config_file, 'r') as nf:
    mqtt_cfg = yaml.safe_load(nf)
mqtt_broker=(mqtt_cfg["mqtt_config"]["mqtt_broker"])
mqtt_port=(mqtt_cfg["mqtt_config"]["mqtt_port"])
mqtt_user=(mqtt_cfg["mqtt_config"]["mqtt_user"])
mqtt_pass=(mqtt_cfg["mqtt_config"]["mqtt_pass"])
mqtt_interval=(mqtt_cfg["mqtt_config"]["mqtt_interval"])
chronothermostats=load_api_config_arg("chronothermostats")
LOGFILE = 'log/mqtt_log'
LOGFORMAT = '%(asctime)-15s %(message)s'
DEBUG=False

if DEBUG:
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=LOGFORMAT)
else:
    logging.basicConfig(filename=LOGFILE, level=logging.INFO, format=LOGFORMAT)

logging.info("Starting")
logging.debug("DEBUG MODE")

def set_payload(arg):
    if arg == "auto":
       payload = {
        "mode": "AUTOMATIC"
        }
    elif arg == "MANUAL":
       payload = {
        "mode": "MANUAL"
        }
    elif arg == "BOOST":
       payload = {
        "mode": "BOOST"
        }
    elif arg == "off":
       payload = {
        "mode": "OFF"
       }
    elif arg == "PROTECTION":
       payload = {
        "mode": "PROTECTION"
       }
    elif arg.replace('.', '', 1).isdigit():
       payload = {
        "mode": "MANUAL",
        "setpoint": arg
       }
    return payload

def runprog(topic, param=None):

    #send_thermostat_cmd(topic,param)
    if send_thermostat_cmd(topic,param):
       payload = set_payload(arg)
       my_topic = topic.replace("cmd", "status")
       logging.debug("my payload:"+payload, "my_topic:"+ my_topic)
       mqttc.publish(my_topic, payload, qos=qos, retain=False)

def on_message(mosq, userdata, msg):
    logging.debug(msg.topic+" "+str(msg.qos)+" "+msg.payload.decode('utf-8'))

    runprog(msg.topic, msg.payload.decode('utf-8'))

def on_connect(mosq, userdata, flags, result_code):
    logging.debug("Connected to MQTT broker, subscribing to topics...")
    for topic in topiclist:
        mqttc.subscribe(topic, qos)


def on_disconnect(mosq, userdata, rc):
    logging.debug("mqtt disconnects")
    time.sleep(10)

if __name__ == '__main__':

    userdata = {
    }

    topiclist=[]
    for i in chronothermostats:
        mqtt_cmd_topic=(i)['chronothermostat']['mqtt_cmd_topic']
        topiclist.append(mqtt_cmd_topic)

    if topiclist is None:
        logging.info("No topic list. Aborting")
        sys.exit(2)

    clientid = "bticino_mqtt" 
    mqttc = paho.Client(clientid, clean_session=False)


    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect

    mqttc.will_set('clients/mqtt-launcher', payload="Adios!", qos=0, retain=False)

    # Delays will be: 3, 6, 12, 24, 30, 30, ...
    #mqttc.reconnect_delay_set(delay=3, delay_max=30, exponential_backoff=True)

    mqttc.username_pw_set(mqtt_user,mqtt_pass)

#    if cf.get('mqtt_tls') is not None:
#        mqttc.tls_set()

    mqttc.connect(mqtt_broker, mqtt_port, 60)

    while True:
        try:
            mqttc.loop_forever()
        except socket.error:
            time.sleep(5)
        except KeyboardInterrupt:
            sys.exit(0)
