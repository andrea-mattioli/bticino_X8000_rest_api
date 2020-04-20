from bticino import rest,subscribe_c2c,load_api_config_arg
import paho.mqtt.client as mqtt
import yaml
import json
config_file = 'config/mqtt_config.yml'
with open(config_file, 'r') as f:
    cfg = yaml.safe_load(f)
mqtt_broker=(cfg["mqtt_config"]["mqtt_broker"])
mqtt_port=(cfg["mqtt_config"]["mqtt_port"])
mqtt_user=(cfg["mqtt_config"]["mqtt_user"])
mqtt_pass=(cfg["mqtt_config"]["mqtt_pass"])
mqtt_interval=(cfg["mqtt_config"]["mqtt_interval"])
flag_connected = 0
def on_connect(mqtt_client, obj, flags, rc):
    global flag_connected
    flag_connected = 1
    if rc != 0:
        raise mqtt.MQTTException(paho.connack_string(rc))
def on_disconnect():
    global flag_connected
    flag_connected = 0
mqtt_client = mqtt.Client(client_id="C2C_Subscription")
mqtt_client.username_pw_set(mqtt_user,mqtt_pass)
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect(mqtt_broker, mqtt_port, 60)
def send_mqtt_values(c2c_response):
    chronothermostats_stored=load_api_config_arg("chronothermostats")
    for c in chronothermostats_stored:
        topology=c['chronothermostat']['topology']            
        name=c['chronothermostat']['name']            
        mqtt_status_topic=c['chronothermostat']['mqtt_status_topic']
        for chronothermostat in c2c_response['chronothermostats']:
            if topology == chronothermostat['sender']['plant']['module']['id']:
               function=(chronothermostat['function'])
               mode=(chronothermostat['mode'])
               state=(chronothermostat['loadState'])
               setpoint=(chronothermostat['setPoint']['value'])
               programs=(chronothermostat['programs'])
               for prog in programs:
                   program = prog['number']
               thermometers=(chronothermostat['thermometer']['measures'])
               for thermometer in thermometers:
                   temperature = thermometer['value']
               hygrometers=(chronothermostat['hygrometer']['measures'])
               for hygrometer in hygrometers:
                   humidity = hygrometer['value']
               data = json.dumps({ "name": name, "mode" : mode, "function" : function ,  "state" : state, "setpoint" : setpoint, "temperature" : temperature, "humidity" : humidity, "program": program})
               mqtt_client.loop_start()
               mqtt_client.publish(mqtt_status_topic, data, 1)
               mqtt_client.loop_stop()
               mqtt_client.disconnect()
