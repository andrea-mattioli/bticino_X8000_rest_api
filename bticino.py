from flask import  Flask,jsonify,request,session,redirect,render_template,url_for,send_from_directory,Response
import flask
import random
import string
import json
import requests
import yaml
import time
from apscheduler.schedulers.background import BackgroundScheduler


def randomStringDigits(stringLength=32):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))
oauth2_url="https://partners-login.eliotbylegrand.com/authorize"
token_url="https://partners-login.eliotbylegrand.com/token"
devapi_url="https://api.developer.legrand.com/smarther/v2.0"
thermo_url=devapi_url+"/chronothermostat/thermoregulation/addressLocation"
state=randomStringDigits()
config_file = 'config/config.yml'
api_config_file = 'config/smarter.json'
with open(config_file, 'r') as f:
    cfg = yaml.safe_load(f)
client_id=(cfg["api_config"]["client_id"])
client_secret=(cfg["api_config"]["client_secret"])
subscription_key=(cfg["api_config"]["subscription_key"])
redirect_url=(cfg["api_config"]["redirect_url"])
app = Flask(__name__)
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
@app.route('/rest/', methods=['GET', 'POST'])
def rest_api():
    response=rest()
    return Response(response,  mimetype='application/json')

def rest():
    code, access_token, my_plants, chronotermostats, refresh_token = load_api_config()
    chronothermostats_status=[]
    for i in chronotermostats:
        plantid=(i)['chronothermostat']['plant']
        topologyid=(i)['chronothermostat']['topology']
        name=(i)['chronothermostat']['name']
        mode,function,state,setpoint,temperature,temp_unit,humidity = get_status(access_token,plantid,topologyid)
        chronothermostats_status.append({ "name": name, "mode" : mode, "function" : function ,  "state" : state, "setpoint" : setpoint, "temperature" : temperature, "temp_unit" : temp_unit, "humidity" : humidity})
        return chronothermostats_status

@app.route('/get_code')
def get_token(my_url=None):
    my_url = oauth2_url+"?client_id="+client_id+"&response_type=code"+"&state="+state+"&redirect_uri="+redirect_url
    return render_template('index.html', value=my_url)

#def mqtt_rest():
#    code, access_token, plantid, topologyid, refresh_token = load_api_config()
#    mode,function,state,setpoint,temperature,temp_unit,humidity = get_status(access_token,plantid,topologyid,code)
#    response = { "mode" : mode, "function" : function ,  "state" : state, "setpoint" : setpoint, "temperature" : temperature, "temp_unit" : temp_unit, "humidity" : humidity}
#    return json.dumps(response)

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
          code, access_token, my_plants, chronothermostats, refresh_token = load_api_config()
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
            if plant == plant_r:
               for topology in topologys:
                   topologyid=(topology['id'])
                   topologyname=(topology['name'])
                   chronothermostats.append({"chronothermostat":{"plant":plant, "topology":topologyid, "name":topologyname}})
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
            for thermometer in thermometers:
                temperature=thermometer['value']
            hygrometers=(chronothermostat['hygrometer']['measures'])
            for hygrometer in hygrometers:
                humidity=hygrometer['value']
        return mode,function,state,setpoint,temperature,temp_unit,humidity
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def schedule_update_token():
    f_refresh_token()
    scheduler = BackgroundScheduler()
    scheduler.add_job(f_refresh_token, 'interval', minutes=50)
    scheduler.start()

schedule_update_token()
@app.route('/callback/')
def callback():
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
       my_value_tamplate=rest()
       return render_template('info.html', j_response=my_value_tamplate)
    else:
       return "something went wrong"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5588)
