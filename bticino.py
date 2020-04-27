from flask import  Flask,jsonify,request,session,redirect,render_template,url_for,send_from_directory,Response
import flask
import random
import string
import json
import requests
import yaml
import time
import threading
import os
import re
import sys
import shutil
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
from pathlib import Path
def randomStringDigits(stringLength=32):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))
oauth2_url="https://partners-login.eliotbylegrand.com/authorize"
token_url="https://partners-login.eliotbylegrand.com/token"
devapi_url="https://api.developer.legrand.com/smarther/v2.0"
thermo_url=devapi_url+"/chronothermostat/thermoregulation/addressLocation"
state=randomStringDigits()
config_file = 'config/config.yml'
mqtt_config_file = 'config/mqtt_config.yml'
api_config_file = ''
tmp_api_config_file = 'config/smarter.json'
static_api_config_file = 'config/.bticino_smarter/smarter.json'
subscribe_c2c=False
use_ssl=False
flag_connected = 0

def check_config_file():
    global api_config_file
    Path("config/.bticino_smarter/").mkdir(parents=True, exist_ok=True)
    if not os.path.exists(static_api_config_file) or os.path.getsize(static_api_config_file) == 0:
       api_config_file = 'config/smarter.json'
       return True
    else:
       api_config_file = 'config/.bticino_smarter/smarter.json'
       return False

check_config_file()
    
with open(config_file, 'r') as f:
    cfg = yaml.safe_load(f)
client_id=(cfg["api_config"]["client_id"])
client_secret=(cfg["api_config"]["client_secret"])
subscription_key=(cfg["api_config"]["subscription_key"])
redirect_url=(cfg["api_config"]["redirect_url"])
api_user=(cfg["api_config"]["api_user"])
api_pass=(cfg["api_config"]["api_pass"])
subscribe_c2c=(cfg["api_config"]["subscribe_c2c"])
use_ssl=(cfg["api_config"]["use_ssl"])
dns = re.sub(r'(.*://)?([^:?]+).*', '\g<2>', redirect_url)

with open(mqtt_config_file, 'r') as nf:
    mqtt_cfg = yaml.safe_load(nf)
mqtt_broker=(mqtt_cfg["mqtt_config"]["mqtt_broker"])
mqtt_port=(mqtt_cfg["mqtt_config"]["mqtt_port"])
mqtt_user=(mqtt_cfg["mqtt_config"]["mqtt_user"])
mqtt_pass=(mqtt_cfg["mqtt_config"]["mqtt_pass"])
mqtt_interval=(mqtt_cfg["mqtt_config"]["mqtt_interval"])

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    api_user: generate_password_hash(api_pass)
}

def check_empty_item(item):
    json_object=get_json()
    if len(json_object['api_requirements'][item]) < 1:
       return True
    else:
       return False
#write json file
def get_json():
    a_file = open(api_config_file, "r")
    json_object = json.load(a_file)
    a_file.close()
    return json_object
def write_json(json_object):
    a_file = open(api_config_file, "w")
    json.dump(json_object, a_file)
    a_file.close()
def update_api_config_file_code(code):
    json_object=get_json()
    json_object['api_requirements']['code'] = code
    write_json(json_object)
def update_api_config_file_access_token(access_token):
    json_object=get_json()
    json_object['api_requirements']['access_token'] = access_token
    write_json(json_object)
def update_api_config_file_refresh_token(refresh_token):
    json_object=get_json()
    json_object['api_requirements']['refresh_token'] = refresh_token
    write_json(json_object)
def update_api_config_file_my_plants(my_plants):
    json_object=get_json()
    json_object['api_requirements']['my_plants'] = my_plants
    write_json(json_object)
def update_api_config_file_chronothermostats(chronothermostats):
    json_object=get_json()
    json_object['api_requirements']['chronothermostats'] = chronothermostats
    write_json(json_object)
#end write json file
def load_api_config():
    json_object=get_json()
    code = json_object['api_requirements']['code']
    access_token = json_object['api_requirements']['access_token']
    refresh_token = json_object['api_requirements']['refresh_token']
    my_plants = json_object['api_requirements']['my_plants']
    chronothermostats = json_object['api_requirements']['chronothermostats']
    return code, access_token, my_plants, chronothermostats, refresh_token
def load_api_config_arg(arg):
    json_object=get_json()
    if arg == "code":
       arg = json_object['api_requirements']['code']
    if arg == "access_token":
       arg = json_object['api_requirements']['access_token']
    if arg == "refresh_token":
       arg = json_object['api_requirements']['refresh_token']
    if arg == "my_plants":
       arg = json_object['api_requirements']['my_plants']
    if arg == "chronothermostats":
       arg = json_object['api_requirements']['chronothermostats']
    return arg 
@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False
@app.route('/rest/', methods=['GET', 'POST'])
@auth.login_required
def rest_api():
    response=rest()
    if subscribe_c2c:
       parse_response(json.dumps(response))   
    return Response(json.dumps(response),  mimetype='application/json')
@app.route('/info')
@auth.login_required
def info():
    my_value_tamplate=rest()
    return render_template('info.html', j_response=my_value_tamplate)

@app.route('/file_conf')
@auth.login_required
def dirtree():
    with open(api_config_file, 'r') as f:
       smarter_f_conf=f.read()
    with open(mqtt_config_file, 'r') as f:
       mqtt_f_conf=f.read()
    with open(config_file, 'r') as f:
       api_f_conf=f.read()
    return render_template('file_conf.html', smarter_f_conf=smarter_f_conf, mqtt_f_conf=mqtt_f_conf, api_f_conf=api_f_conf, mimetype='text/plain')

def rest():
    access_token=load_api_config_arg("access_token")
    chronothermostats=load_api_config_arg("chronothermostats")
    chronothermostats_status=[]
    for i in chronothermostats:                                                         
        plantid=(i)['chronothermostat']['plant']                                        
        topologyid=(i)['chronothermostat']['topology']                                  
        name=(i)['chronothermostat']['name']                                            
        c2c=(i)['chronothermostat']['c2c']                                              
        mqtt_status_topic=(i)['chronothermostat']['mqtt_status_topic']                  
        mqtt_cmd_topic=(i)['chronothermostat']['mqtt_cmd_topic']                        
        mode,function,state,setpoint,temperature,temp_unit,humidity,my_program = get_status(access_token,plantid,topologyid)
        chronothermostats_status.append({ "name": name, "mode" : mode, "function" : function ,  "state" : state, "setpoint" : setpoint, "temperature" : temperature, "temp_unit" : temp_unit, "humidity" : humidity, "program" : my_program, "c2c-subscription": c2c, "mqtt_status_topic":mqtt_status_topic, "mqtt_cmd_topic":mqtt_cmd_topic})
    return chronothermostats_status

@app.route('/')
@auth.login_required
def get_token(my_url=None):
    my_url = oauth2_url+"?client_id="+client_id+"&response_type=code"+"&state="+state+"&redirect_uri="+redirect_url
    return render_template('index.html', code_url=my_url)

def get_access_token(code):
    body = {
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": code,
            "client_secret": client_secret,
        }
    response = requests.request("POST", token_url, data = body)
    access_token = json.loads(response.text)['access_token']
    refresh_token = json.loads(response.text)['refresh_token']
    return access_token, refresh_token

def f_refresh_token():
       if not check_empty_item("refresh_token"):
          refresh_token=load_api_config_arg("refresh_token")
          body = {
                  "client_id": client_id,
                  "grant_type": "refresh_token",
                  "refresh_token": refresh_token,
                  "client_secret": client_secret,
              }
          response = requests.request("POST", token_url, data = body)
          access_token = json.loads(response.text)['access_token']
          update_api_config_file_access_token(access_token)
          refresh_token = json.loads(response.text)['refresh_token']
          update_api_config_file_refresh_token(refresh_token)

def get_plants(access_token):
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key ,
        'Authorization': 'Bearer '+access_token,
    }
    payload = ''
    try:
        response = requests.request("GET", devapi_url+"/plants", data = payload, headers = headers)
        plants = json.loads(response.text)['plants']
        my_plants=[]
        for plan in plants:
            my_plants.append(plan['id'])
        return my_plants
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def get_topology(access_token,my_plants):
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key ,
        'Authorization': 'Bearer '+access_token,
    }
    payload = ''
    try:
        chronothermostats=[]
        for plant in my_plants:
            response = requests.request("GET", devapi_url+"/plants/"+plant+"/topology", data = payload, headers = headers)
            topologys = json.loads(response.text)['plant']['modules']
            plant_r = json.loads(response.text)['plant']['id']
            if f_c2c_subscribe(access_token,plant):
               c2c = "Enable"
            else:
               c2c = "Disable"
            if plant == plant_r:
               for topology in topologys:
                   topologyid=(topology['id'])
                   topologyname=(topology['name'])
                   mqtt_status_topic="/bticino/"+topologyid+"/status"
                   mqtt_cmd_topic="/bticino/"+topologyid+"/cmd"
                   chronothermostats.append({"chronothermostat":{"plant":plant, "topology":topologyid, "name":topologyname, "c2c":c2c, "mqtt_status_topic":mqtt_status_topic, "mqtt_cmd_topic":mqtt_cmd_topic}})
        return chronothermostats
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def get_status(access_token,plantid,topologyid):
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key ,
        'Authorization': 'Bearer '+access_token,
    }
    payload = ''
    try:
        response = requests.request("GET", thermo_url+"/plants/"+plantid+"/modules/parameter/id/value/"+topologyid, data = payload, headers = headers)
        chronothermostats = json.loads(response.text)['chronothermostats']
        for chronothermostat in chronothermostats:
            function=(chronothermostat['function'])
            mode=(chronothermostat['mode'])
            state=(chronothermostat['loadState'])
            setpoint=(chronothermostat['setPoint']['value'])
            temp_unit=(chronothermostat['temperatureFormat'])
            thermometers=(chronothermostat['thermometer']['measures'])
            programs=(chronothermostat['programs'])
            for program in programs:
                my_program=program['number']
            for thermometer in thermometers:
                temperature=thermometer['value']
            hygrometers=(chronothermostat['hygrometer']['measures'])
            for hygrometer in hygrometers:
                humidity=hygrometer['value']
        return mode,function,state,setpoint,temperature,temp_unit,humidity,my_program
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def f_c2c_subscribe(access_token,plantid):
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key ,
        'Authorization': 'Bearer '+access_token,
        'Content-Type': 'application/json',
    }
    if subscribe_c2c:
       payload = {
                  "EndPointUrl": redirect_url,
                  "description": "Rest Api",
                 }
       try:
          response = requests.request("POST", devapi_url+"/plants/"+plantid+"/subscription", data = json.dumps(payload), headers = headers)
          if response.status_code == 201:
             return True
          if response.status_code == 409:
             return True
          else:
             return False
       except Exception as e:
           print("[Errno {0}] {1}".format(e.errno, e.strerror))
           return False
    else:
        payload = ''
        try:
           response = requests.request("GET", devapi_url+"/subscription", data = payload, headers = headers)
           list_endpoints=[]
           list_subscription=[]
           for j in json.loads(response.text):
               if redirect_url == j['EndPointUrl']:
                  subscriptionId=(j['subscriptionId'])
                  response = requests.request("DELETE", devapi_url+"/plants/"+plantid+"/subscription/"+subscriptionId, data = payload, headers = headers)
                  if response.status_code == 200:
                     return False
                  else:
                     return True
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
            return True

def set_payload(arg,function,mode,setPoint,temp_unit,program):
    if arg == "auto":
       payload = {
        "function": function,
        "mode": "automatic",
        "setPoint": {
          "value": setPoint,
          "unit": temp_unit
        },
        "programs": [
          {
            "number": program
          }
        ]
       }
    elif arg == "MANUAL":
       payload = {
        "function": function,
        "mode": "manual",
        "setPoint": {
          "value": setPoint,
          "unit": temp_unit
        }
       }
    elif arg == "BOOST":
       payload = {
        "function": function,
        "mode": "boost",
        "setPoint": {
          "value": setPoint,
          "unit": temp_unit
        }
       }
    elif arg == "off":
       payload = {
        "function": function,
        "mode": "off",
       }
    elif arg == "PROTECTION":
       payload = {
        "function": function,
        "mode": "protection",
       }
    elif arg == "heat":
       payload = {
        "function": "heating",
        "mode": mode,
        "setPoint": {
          "value": setPoint,
          "unit": temp_unit
        },
        "programs": [
          {
            "number": program
          }
        ]
       }
    elif arg == "cool":
       payload = {
        "function": "cooling",
        "mode": mode,
        "setPoint": {
          "value": setPoint,
          "unit": temp_unit
        },
        "programs": [
          {
            "number": program
          }
        ]
       }
    elif arg.replace('.', '', 1).isdigit():
       payload = {
        "function": function,
        "mode": "manual",
        "setPoint": {
          "value": arg,
          "unit": temp_unit
        },
        "programs": [
          {
            "number": program
          }
        ]
       }
    return payload

def send_thermostat_cmd(mqtt_cmd_topic, arg):
    access_token=load_api_config_arg("access_token")
    chronothermostats=load_api_config_arg("chronothermostats")
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key ,
        'Authorization': 'Bearer '+access_token,
        'Content-Type': 'application/json',
    }
    try:
       get_actual_state=rest()
       for i in get_actual_state:
           my_mqtt_cmd_topic=(i)['mqtt_cmd_topic']
           for j in chronothermostats:
               my_stored_mqtt_cmd_topic=(j)['chronothermostat']['mqtt_cmd_topic']
               if mqtt_cmd_topic == my_mqtt_cmd_topic == my_stored_mqtt_cmd_topic:
                  plantid=(j)['chronothermostat']['plant']
                  topologyid=(j)['chronothermostat']['topology']
                  mode=(i)['mode']
                  function=(i)['function']
                  setPoint=(i)['setpoint']
                  temp_unit=(i)['temp_unit']
                  program=str((i)['program'])
       payload = set_payload(arg,function,mode,setPoint,temp_unit,program)
       response = requests.request("POST", devapi_url+"/chronothermostat/thermoregulation/addressLocation/plants/"+plantid+"/modules/parameter/id/value/"+topologyid, data = json.dumps(payload), headers = headers)
       if response.status_code == 200:
          return True
       else:
          return False
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        return False
    
def schedule_update_token():
    f_refresh_token()
    scheduler = BackgroundScheduler()
    scheduler.add_job(f_refresh_token, 'interval', minutes=50)
    scheduler.start()
schedule_update_token()

def b_mqtt(mqtt_status_topic, data):
    subprocess.call(["mosquitto_pub", "-h", str(mqtt_broker), "-p", str(mqtt_port), "-u", str(mqtt_user), "-P", str(mqtt_pass), "-m", data, "-t", str(mqtt_status_topic), "-i", "C2C_Subscription"])

def mqtt_get_value():
    data=rest()
    for i in data:
        mqtt_status_topic=(i['mqtt_status_topic'])
    b_mqtt(mqtt_status_topic,data)
    
def mqtt_scheduler():
    mqtt_get_value()
    scheduler = BackgroundScheduler()
    scheduler.add_job(mqtt_get_value, 'interval', minutes=mqtt_interval)
    scheduler.start()
if not subscribe_c2c:
   mqtt_scheduler()

def parse_response(data):
    chronothermostats_stored=load_api_config_arg("chronothermostats")
    for j in json.loads(data):
        try:
           c2c_response=(j['data'])
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
                      mqtt_data = json.dumps({ "name": name, "mode" : mode, "function" : function ,  "state" : state, "setpoint" : setpoint, "temperature" : temperature, "humidity" : humidity, "program": program})
                      b_mqtt(mqtt_status_topic,mqtt_data)
        except:
           name = (j['name'])
           mode = (j['mode'])
           function = (j['function'])
           state = (j['state'])
           setpoint = (j['setpoint'])
           temperature = (j['temperature'])
           humidity = (j['humidity'])
           mqtt_status_topic = (j['mqtt_status_topic'])
           mqtt_data = json.dumps({ "name": name, "mode" : mode, "function" : function ,  "state" : state, "setpoint" : setpoint, "temperature" : temperature, "humidity" : humidity })
           b_mqtt(mqtt_status_topic,mqtt_data)

@app.route('/callback/', methods=['GET', 'POST'])
def callback():
    if request.method == 'POST':
       parse_response(request.data)
       return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    else:
        code = request.args.get('code')
        access_token, refresh_token = get_access_token(code)
        if access_token != None and refresh_token != None:
           my_plants=get_plants(access_token)
           chronothermostats=get_topology(access_token,my_plants)
           update_api_config_file_code(code)
           update_api_config_file_access_token(access_token)
           update_api_config_file_refresh_token(refresh_token)
           update_api_config_file_my_plants(my_plants)
           update_api_config_file_chronothermostats(chronothermostats)
           if check_config_file():
              shutil.move(os.path.join(tmp_api_config_file), os.path.join(static_api_config_file))
           check_config_file()
           my_value_tamplate=rest()
           return render_template('info.html', j_response=my_value_tamplate)
        else:
           return "something went wrong"

if __name__ == '__main__':
    def find_cert():
        try:
           certs = []
           for path in Path('/ssl/').rglob('fullchain.pem'):
               ps = subprocess.Popen(["openssl", "x509", "-noout", "-text", "-in", str(path)], stdout=subprocess.PIPE)
               output = subprocess.check_output(["grep", "-i", "DNS"], stdin=ps.stdout)
               if dns in str(output):
                  certs.append(path)
           system_cert = max(certs, key=os.path.getctime)
           system_cert_path = os.path.dirname(system_cert)
           ps = subprocess.Popen(["openssl", "x509", "-noout", "-modulus", "-in", str(system_cert)], stdout=subprocess.PIPE)
           md5_cert = subprocess.check_output(["openssl", "md5"], stdin=ps.stdout)
           for key in Path(os.path.dirname(system_cert)).rglob('privkey.pem'):
               ps = subprocess.Popen(["openssl", "rsa", "-noout", "-modulus", "-in", str(key)], stdout=subprocess.PIPE)
               md5_key = subprocess.check_output(["openssl", "md5"], stdin=ps.stdout)
               if md5_key == md5_cert:
                  system_key = key
           print(system_cert, system_key)
           return(system_cert, system_key)
        except:
               print("No valid certificate found, please use ssl_enable = false")
               sys.exit(1)
    if use_ssl: 
       system_cert,system_key=find_cert()
       app.run(debug=True, host='0.0.0.0', port=5588, ssl_context=(system_cert, system_key))
    else:
       app.run(debug=True, host='0.0.0.0', port=5588)
