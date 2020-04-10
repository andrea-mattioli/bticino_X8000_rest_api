# bticino_X8000_rest_api
Chronothermostat Bticino X8000 Rest Api

[![stable](http://badges.github.io/stability-badges/dist/stable.svg)](http://github.com/badges/stability-badges)

## 1. First steps

### 1.1. Register a Developer account
Sign up for a new Developer account on Works with Legrand website (https://developer.legrand.com/login).

### 1.2. Subscribe to Legrand APIs
Sign in, go to menu "API > Subscriptions" and make sure you have "Starter Kit for Legrand APIs" subscription activated; if not, activate it.

### 1.3. Register a new application
Go to menu "User > My Applications" and click on "Create new" to register a new application:
- Insert a valid **public** URL in "First Reply Url". 
- Make sure to tick the checkbox near scopes `comfort.read` and `comfort.write`

Submit your request and wait for a response via email from Legrand (it usually takes 1-2 days max).
If your app has been approved, you should find in the email your "Client ID" and "Client Secret" attributes.

```
Public Url = https://myWebServerIP:myWebServerPort/rest
```
```
First Reply Url = https://myWebServerIP:myWebServerPort/callback
```
![Alt text](/../test/screenshots/app1.png?raw=true "App Register")
![Alt text](/../test/screenshots/app2.png?raw=true "App Register")
