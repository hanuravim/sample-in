"""

this automation runbook is to automate DB user creation in a given server and DB on azure 

"""

from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.common.credentials import ServicePrincipalCredentials
import azure.mgmt.resource
import psycopg2
import json
import sys 
import re
import os

def createhostentry():
    constring="host=gav-ne-ine-qa-postgresqlarmdemo.postgres.database.azure.com user=geinadmin@gav-ne-ine-qa-postgresqlarmdemo dbname=postgres  password= admin@123"
    client = KeyVaultClient(KeyVaultAuthentication(auth_callback)) 
    secret_bundle1 = client.set_secret("https://gav-cu-ine-dev-kvrmdemo.vault.azure.net/", "dbhostconstring", constring)

#Util functions . 
def fixJSON(string):
  string   = re.sub(r"[\n\t\s]*", "", string)
  res = re.sub(r"([^{}:,]+):([^{}:,]+),?", r'"\1":"\2",', string )
  res = re.sub('"[ ]*,[ ]*}', '"}', res)
  # and empty string
  res = re.sub("\"(''|\")\"", '""', res)
  # property : {...}
  res = re.sub(r"([^{}:,]+)(?=:{)", r'"\1"', res )
  return res.replace('\"[\",',"[")

def gen_password(length=8, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"):
    random_bytes = os.urandom(length)
    len_charset = len(charset)
    indices = [int(len_charset * (ord(byte) / 256.0)) for byte in random_bytes]
    return "".join([charset[index] for index in indices])

def gen_user(prefix="",length=8, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"):
    random_bytes = os.urandom(length)
    len_charset = len(charset)
    indices = [int(len_charset * (ord(byte) / 256.0)) for byte in random_bytes]
    return "".join([charset[index] for index in indices])    
# End Util functions .


#DB connnection info- This can come from keyvault as well in final code 
def getazurepostgrsDBconString():
     host = "gav-ne-ine-qa-postgresqlarmdemo.postgres.database.azure.com"
     user = "geinadmin@gav-ne-ine-qa-postgresqlarmdemo"
     dbname = "postgres"
     password = "admin@123"
     #sslmode = "require"
 
     conn_string = "host={0} user={1} dbname={2} password={3} ".format(host, user, dbname, password)
     return(conn_string)
#conn=psycopg2.connect(getazurepostgrsDBconString())


def get_Dbconnection():
    constring=getazurepostgrsDBconString()
    #conn = psycopg2.connect(constring) 
   # cursor = conn.cursor
   # return conn

credentials = None
#this will go as the runbook will run under runas most probably will discuess with GE/hanu security  bob 
def auth_callback(server, resource, scope):
    credentials = ServicePrincipalCredentials(
        client_id = '',
        secret = '',
        tenant = '',
        resource = "https://vault.azure.net"
    )
    token = credentials.token
    return token['token_type'], token['access_token']




 # end of method 

def getjsonforuserpwd():
    usr=gen_user()
    pwd=gen_password()
    udata = {}
    udata["username"] = usr
    udata["password"] = pwd
    return json.dumps(udata)

def getkv_secret(keyname,keyversion=""):
    client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
    secret_bundle =  client.get_secret("https://gav-cu-ine-dev-kvrmdemo.vault.azure.net/", keyname, keyversion)
    return(secret_bundle.value)

def setkv_secret(keyname,secretvalue):
    client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
    secret_bundle1 = client.set_secret("https://gav-cu-ine-dev-kvrmdemo.vault.azure.net/", keyname, secretvalue)
    return(secret_bundle1)

def GetKeyVaultDBKeys(keyname,genkey,keyversion=""):
 client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
 
 if genkey=="true":
    #print "genrate new key"
    secretvalue=getjsonforuserpwd() 
    secret_bundle1 = client.set_secret("https://gav-cu-ine-dev-kvrmdemo.vault.azure.net/", keyname, secretvalue)
 #print secret_bundle1
 secret_bundle =  client.get_secret("https://gav-cu-ine-dev-kvrmdemo.vault.azure.net/", keyname, keyversion)
 #print secret_bundle.value + "getresult"

 return(secret_bundle.value)

conn=psycopg2.connect(getazurepostgrsDBconString())
#print(GetKeyVaultDBKeys())
def createDB(dbname,usr,pwd,prefix=""):
    create_Db_cmd = ("CREATE ROLE %s WITH LOGIN CREATEDB PASSWORD '%s'" % (usr, pwd))
    dbname=prefix+dbname
    #print "dbname:"+dbname
    cursor.execute("SELECT COUNT(*) = 0 FROM pg_catalog.pg_database WHERE LOWER(datname) = LOWER('{0}')".format(dbname))
    #print "SELECT COUNT(*) = 0 FROM pg_catalog.pg_database WHERE datname = '{0}'".format(dbname)
    not_exists_row = cursor.fetchone()
    Db_not_exists = not_exists_row[0]
    #print "Db_not_exists "+ Db_not_exists
    #print 'CREATE DATABASE {0}'.format(dbname)
    if Db_not_exists:
        #print "dbnotexist"+dbname
        cursor.execute('CREATE DATABASE {0}'.format(dbname))
    #cursor.close()
    createUser(dbname,usr,pwd)
#ALTER USER armdemo PASSWORD 'xxxxxx';
	
def createUser(dbname,usr,pwd): 
    check_user_cmd = ("SELECT COUNT(*) = 0 FROM pg_roles WHERE LOWER(rolname)=LOWER('%s')" % (usr))
    create_user_cmd = ("CREATE ROLE %s WITH LOGIN CREATEDB PASSWORD '%s'" % (usr, pwd))
    update_user_pwd =("ALTER USER %s  PASSWORD  '%s'" % (usr, pwd))
    #GRANT ALL PRIVILEGES ON DATABASE <newdb> TO <db_user>;
    grant_user_permission =("GRANT ALL PRIVILEGES ON DATABASE %s TO %s" % (dbname, usr))     #TODO:need to grant proper permission not ALL
    cursor.execute(check_user_cmd)
    not_exists_row = cursor.fetchone()
    usr_not_exists = not_exists_row[0]
    if usr_not_exists:
        cursor.execute(create_user_cmd)        
    else:
        cursor.execute(update_user_pwd)
    cursor.execute(grant_user_permission) # grant permission ever time ..No need to check if its granted as it will take more totel num of queries widout anygains
    
    
def applykeyvault(jobj):
   #print "inapplukeyvault"
   for item in jobj["database"]:
       #print "inapplukeyvault-for"
       generatekey=item["generatekey"] 
       #print generatekey  
       keyname=item["kvkey"]
      # item["hostkey"] =  getkv_secret(item["hostkey"])  
       #generatekey="true" 
       #if generatekey=="true":    
         # secretvalue=getjsonforuserpwd() 
          #secret_bundle1 = setkv_secret(keyname, secretvalue) 
       #secret_bundle =  getkv_secret(keyname)      
       uobj=json.loads(GetKeyVaultDBKeys(keyname,generatekey))     
       item["username"]=uobj["username"]
       item["password"]=uobj["password"]
       
   return jobj    



def Dd_proviosning():
    #print sys.argv[1]
    jsonstr=fixJSON(str(sys.argv[1]))
    #print jsonstr
    jobj=json.loads(jsonstr)
    jobj=applykeyvault(jobj)
 
    for item in jobj["database"]:
        #print dname
        dname=item["name"]
        usr=item["username"]
        pwd =item["password"]
        prefix=""
        if item["tenants"]=="true":
            for tenent in jobj["tenants"]:
                #print tenant
                tanentdbname=tenent["name"]
                prefix= dname+"_"
                createDB(tanentdbname,usr,pwd,prefix)  
            # create user for each tanent
        else:
             createDB(dname,usr,pwd)   
           
    return jobj       
   # print jobj["Datbase"]
try:  
    conn = psycopg2.connect(getazurepostgrsDBconString())
    conn.autocommit = True
    cursor = conn.cursor()
    objj=Dd_proviosning() 
    print json.dumps(objj) 
except Exception as e:
    print('Error:', e)  
finally:
    conn.commit()
    cursor.close()
    conn.close()       
   


