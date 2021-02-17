import sys
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def randomStringDigits(stringLength=32):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))
state=randomStringDigits()
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36 Edge/12.0')
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=chrome_options)
email=sys.argv[1]
passwd=sys.argv[2]
haip=sys.argv[3]
client_id=sys.argv[4]
oauth2_url="https://partners-login.eliotbylegrand.com/authorize"
redirect_code_url="http://%s:5588/callback"%(haip)
my_url = "%s?client_id=%s&response_type=code&state=%s&redirect_uri=%s"%(oauth2_url,client_id,state,redirect_code_url)
timeout = 10
def accept():
    try:
        accept_b=driver.find_element_by_xpath("//input[@class='btn btn-primary pull-left']");
        if accept_b.is_displayed():
            accept_b.click()
    except NoSuchElementException:
        pass

def Username():
    global driver
    global email
    username = driver.find_element_by_xpath("//input[@id='logonIdentifier']");
    username.clear()
    username.send_keys(email)

def Password():
    global driver
    global passwd
    password = driver.find_element_by_xpath("//input[@id='password']");
    password.clear()
    password.send_keys(passwd)
    password.send_keys(u'\ue007')

driver.get(my_url)
try:
    element_present = EC.presence_of_element_located((By.ID, 'logonIdentifier'))
    WebDriverWait(driver, timeout).until(element_present)
except TimeoutException:
    print("Timed out waiting for page to load")
    sys.exit(1)
finally:
    if "login.eliotbylegrand.com" in driver.current_url:       
        Username()
        Password()
        try:
            element_present = EC.presence_of_element_located((By.ID, 'user-consent__opt-in'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")
            sys.exit(1)
        finally:
            accept()
            if "5588/callback" in driver.current_url:
                print("Successfully login to Legrand")                                                                        
                sys.exit(0)
            else:
                print("Can't Login to Legrand")
                sys.exit(1)
    driver.close()    
