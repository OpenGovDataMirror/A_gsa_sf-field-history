
# Salesforce Field History Retrieval
A lightweight Python command line utility that backs up Salesforce Field History data for long term storage. 

# Setup
## Python Setup
Install Requests library, http://docs.python-requests.org/en/master/user/install/

## Salesforce Connected App
You will need to create a Salesforce Connected app

* Go to Setup > Create > Apps
* Scroll down to Connected Apps, click New
* Enter the App Name, sf-field-history
* Enter Basic Information as necessary. Best practice is to use a service account rather than assigning to a specific administrator so that application access is not interrupted if an administrator leaves your team.
* Callback URL is required but is not necessary for this application. Enter the URL of your salesforce instance.
* Set OAuth scopes:
	* Access and Manage Your Data (api). Feel free to create custom permissions as needed.
* None of the information under Custom Connected App Handler, Mobile App Settings, or Canvas App Settings is required
* Click Save

## Credential and Org Management
* Copy the .sample.env file and rename to .env.
* Add site URI, do not include https://
* Enter user credentials including OAuth Consumer Key and Consumer Secret

# Requirements
* Python v2.7 or greater
* User with Salesforce API access

# Usage

## Run Locally
Retrieve logs for a given environment
```
$ python retrieveHistory.py {orgname}
>>Fetching logs from, orgname.cs32.my.salesforce.com
```
Run in debug mode
```
$ python retrieveHistory.py orgname -d
Fetching logs from, myOrgName.cs32.my.salesforce.com
Debug has been turned on, logs will be stored at logs/20190209-2212.52.log
```
Display list of environments stored in .env
```
$ python retrieveHistory.py -e
The following environments have credentials stored:
  - orgname1
  - orgname2
  - orgname3
You can use one of the sites by entering:

  $ python retrieveHistory.py orgname
```
Display help
```
$ python retrieveHistory.py -h
usage: retrieveHistory.py [-h] [-e] [-d] [orgName]

Salesforce Field History Retrieval This python script will authenticate
against Salesforce and pull json responses containing field history data.
Request responses are logged in the /logs directory. Each run of this app will
generate multiple requests, those requests are merged into a single log file

positional arguments:
  orgName      enter the org key of the environment contained in .env

optional arguments:
  -h, --help   show this help message and exit
  -e, --env    display list of Salesforce environments contained in the .env
               file
  -d, --debug  Prints detailed output to the /logs folder
```

## Setup CRON Job
```
$ crontab -e
0 1 * * * path/to/retrieveHistory.py {orgname}
```

# FAQ & Troubleshooting
**500 Response on sa.authenticate()**
Typically results from outdated OpenSSL library resulting in a TLS 1.0 call. Salesforce requires TLS 1.1 or greater connections. Upgrade OpenSSL library to resolve
