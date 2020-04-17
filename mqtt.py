from bticino import rest
import paho.mqtt.client as mqtt
import yaml
import json
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
config_file = 'config/mqtt_config.yml'
next_reading = time.time()
with open(config_file, 'r') as f:
    cfg = yaml.safe_load(f)
mqtt_broker=(cfg["mqtt_config"]["mqtt_broker"])
mqtt_port=(cfg["mqtt_config"]["mqtt_port"])
mqtt_user=(cfg["mqtt_config"]["mqtt_user"])
mqtt_pass=(cfg["mqtt_config"]["mqtt_pass"])
mqtt_interval=(cfg["mqtt_config"]["mqtt_interval"])
mqtt_state_topic=(cfg["mqtt_config"]["mqtt_state_topic"])
flag_connected = 0
def on_connect(mqtt_client, obj, flags, rc):
    global flag_connected
    flag_connected = 1
    if rc != 0:
        raise mqtt.MQTTException(paho.connack_string(rc))
def on_disconnect():
    global flag_connected
    flag_connected = 0
def f_get_value():
    try:
       data=rest()
       if flag_connected == 1:
          mqtt_client.publish(mqtt_state_topic, data, 1)
       else:
          mqtt_client.connect(mqtt_broker, mqtt_port)
          mqtt_client.publish(mqtt_state_topic, data, 1)
    except:
       pass
def background():
    mqtt_client.loop_forever()
    if flag_connected != 1:
       mqtt_client.connect(mqtt_broker, mqtt_port)
def mqtt_scheduler():
    f_get_value()
    scheduler = BackgroundScheduler()
    scheduler.add_job(f_get_value, 'interval', minutes=mqtt_interval)
    scheduler.start()
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(mqtt_user,mqtt_pass)
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_scheduler()
b = threading.Thread(name='background', target=background)
b.start()
