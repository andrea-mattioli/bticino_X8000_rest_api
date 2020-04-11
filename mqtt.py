from bticino import mqtt_rest
import paho.mqtt.client as mqtt
import yaml
import json
import time
config_file = 'config/mqtt_config.yml'
next_reading = time.time()
with open(config_file, 'r') as f:
    cfg = yaml.safe_load(f)
mqtt_broker=(cfg["mqtt_config"]["mqtt_broker"])
mqtt_port=(cfg["mqtt_config"]["mqtt_port"])
mqtt_user=(cfg["mqtt_config"]["mqtt_user"])
mqtt_pass=(cfg["mqtt_config"]["mqtt_pass"])
mqtt_interval=(cfg["mqtt_config"]["mqtt_interval"])
mqtt_cmd_topic=(cfg["mqtt_config"]["mqtt_cmd_topic"])
mqtt_state_topic=(cfg["mqtt_config"]["mqtt_state_topic"])
def on_connect(mqtt_client, obj, flags, rc):
    mqtt_client.subscribe([mqtt_state_topic,mqtt_cmd_topic])
def on_message(mqtt_client, obj, msg):
    print("message received " ,str(msg.payload.decode("utf-8")))
    print("message topic=",msg.topic)
    print("message qos=",msg.qos)
    print("message retain flag=",msg.retain)
print("Initializing subscriber")
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(mqtt_user,mqtt_pass)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.loop_start()
while True:
   data=mqtt_rest() 
   print(data)
   mqtt_client.publish(mqtt_state_topic, data, 1)
   next_reading += mqtt_interval*60
   sleep_time = next_reading-time.time()
   if sleep_time > 0:
      time.sleep(sleep_time)
