import datetime, getopt, gzip, json, logging, os, requests, shutil, sys, urllib
from FieldHistoryFileWriter import FieldHistoryFileWriter
from requests.auth import HTTPBasicAuth
from SalesforceSobject import SalesforceSobject

"""
Salesforce API
"""
class SalesforceApi:

    def __init__(self,environment):
        self.username = environment['username']
        self.password = environment['password']
        self.securityToken = environment['securityToken']
        self.sfConsumerKey = environment['consumerKey']
        self.sfConsumerSecret = environment['consumerSecret']
        self.sfURL = environment['salesforceURL']
        self.environment = environment
        self.accessToken = ''
        self.logger = logging.getLogger(__name__)
        self.logger.info('SalesforceApi Class initiated')

    def constructHeaders(self, contentType="application/x-www-form-urlencoded"):
        """Creates a header object that gets sent in API requests
        Parameters
        ----------
        contentType : string
            ex: 'text/plain', 'application/xml', 'text/html', 'application/json'

        Returns
        -------
        object
            valid header object
        """
        if self.accessToken != '':
            header = {'Content-Type': 'application/json','Authorization':'Bearer '+self.accessToken}
        else:
            header  = {'Content-Type': 'application/x-www-form-urlencoded'}
        return header


    def authenticate(self):
        """Authenticate against Salesforce using an OAuth connection. Sets the accessToken attribute of the SalesforceApi class
        Parameters
        ----------

        Returns
        -------
        void
        """
        # Login Step 1, Request Access token
        # To do so, you must have created a connected App in Salesforce and have a clientId and clientSecret available along with username, password, and securityToken
        authHeaders = {'Content-Type': 'application/x-www-form-urlencoded'}
        # Constrcut the body of the request for access token

        url = 'https://'+self.sfURL+'/services/oauth2/token'

        payload = {'username': self.username,
                'client_secret': self.sfConsumerSecret,
                'password': self.password+self.securityToken,
                'grant_type': 'password',
                'client_id': self.sfConsumerKey}

        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        rawResponse = requests.request("POST", url, data=payload, headers=headers)

        response = json.loads(rawResponse.text)
        self.logger.debug("Authenticate response, %s", response)
        self.accessToken = response['access_token']

    def getObjects(self):
        """Calls the 'services/data/v37.0/sobjects/' endpoint
        Parameters
        ----------

        Returns
        -------
        json
            sobjects response see, https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_describeGlobal.htm
        """

        # If accessToken is not set, throw error
        if (self.accessToken == ''):
            raise ValueError('accessToken has not been set, run authenticate method to set token')
            exit
        # Set headers
        headers = {'Content-Type': 'application/json','Authorization':'Bearer '+self.accessToken}
        rawResponse = requests.get("https://"+self.sfURL+"/services/data/v37.0/sobjects/", headers=headers)
        response = json.loads(rawResponse.text)

        return response

    def getHistoryObjects(self, data):
        """Parses output of getObjects() and returns only objects that store field history

        Parameters
        ----------
        data : object
            ex:
            {
              "encoding" : "UTF-8",
              "maxBatchSize" : 200,
              "sobjects" : [ {
                "activateable" : false,
                "custom" : false,
                "customSetting" : false,
                "createable" : true,
                "deletable" : true,
                "deprecatedAndHidden" : false,
                "feedEnabled" : true,
                "keyPrefix" : "001",
                "label" : "Account",
                "labelPlural" : "Accounts",
                "layoutable" : true,
                "mergeable" : true,
                "mruEnabled" : true,
                "name" : "Account",
                "queryable" : true,
                "replicateable" : true,
                "retrieveable" : true,
                "searchable" : true,
                "triggerable" : true,
                "undeletable" : true,
                "updateable" : true,
                "urls" : {
                  "sobject" : "/services/data/v37.0/sobjects/Account",
                  "describe" : "/services/data/v37.0/sobjects/Account/describe",
                  "rowTemplate" : "/services/data/v37.0/sobjects/Account/{ID}"
                }
              }
              ]
            }


        Returns
        ------------
        Array of SalesforceSobjects
        """
        # badHistoryObjects contains a list of objects that end in 'History' but are not valid Field History objects
        badHistoryObjects = ['ActivityHistory', 'Application__VersionHistory', 'Blog__VersionHistory', 'KnowledgeArticleVersionHistory','LinkedArticleHistory','LoginHistory','OpportunityHistory','ProcessInstanceHistory','Product2History','Publication__VersionHistory','VerificationHistory']
        historyObjects = []
        for objects in data["sobjects"]:
            if objects["name"].endswith("History") and objects["name"] not in badHistoryObjects:
                describedSobject = self.describeSObjects(objects["urls"]["describe"])
                sObjectFields = self.getSObjectFields(describedSobject)
                newSobject = SalesforceSobject(objects["name"], objects["urls"], self.sfURL, sObjectFields)
                historyObjects.append(newSobject)

        return historyObjects

    def getSObjectFields(self, describedSObject):
        """Given output of the describe endpoint '/services/data/v37.0/sobjects/{objName}/describe', returns an array of fields
'
        Parameters
        ----------
        describedSObject : object
            output from /describe

        Returns
        -------
        array
            list of fields
        """
        fieldsArray = []
        for field in describedSObject["fields"]:
            fieldsArray.append(field["name"])
        return fieldsArray

    def describeSObjects(self, uri):
        """Retrieves a description of a given sObject
'
        Parameters
        ----------
        uri : string
            uri

        Returns
        -------
        object
            output from endpoint
        """
        headers = self.constructHeaders()
        rawResponse = requests.get("https://"+self.sfURL+uri, headers=headers)
        response = json.loads(rawResponse.text)
        self.logger.debug("DescribeSobjects response, %s", response)
        return response

    def getAllRecords(self, objectName):
        """ given an object name, iterates over all records and saves to csv

        Parameters
        -----------
        param: objectName
            API name of an object

        Returns
        -------
        void
        """

        fields = ["Id","IsDeleted","ParentId", "CreatedById", "CreatedDate", "Field", "OldValue", "NewValue"]
        nextRecordsUrl = 'true'
        while nextRecordsUrl != '':
            self.query(fields,objectName)


    def query(self, fields, objectName):
        """queries the Salesforce api

        Parameters
        -----------
        param: fields
            array of fields for select statement
        param: objectName

        """
        headers = self.constructHeaders()
        selectStatement = self.constructSelectStatement(fields)
        # post the request
        rawResponse = requests.get("https://"+self.sfURL+"/services/data/v32.0/queryAll?q="+selectStatement+" FROM "+objectName, headers=headers)
        response = json.loads(rawResponse.text)
        return response

    def getNextRecords(self, uri):
        """provided a nextRecordsUrl, runs query and returns results as json object

        Parameters
        -----------
        param: uri
            A Salesforce proivded uri that pages through records. Ex, "/services/data/v20.0/query/01gD0000002HU6KIAW-2000"

        Return
        ------
        json
            response
        """
        headers = self.constructHeaders()
        rawResponse = requests.get("https://"+self.sfURL+uri, headers=headers)
        response = json.loads(rawResponse.text)
        return response

    def hasNextRecords(self, query):
        """Checks whether a query response contains a nextRecordsUrl

        Parameters
        -----------
        param: query
            output from a RESTful query request

        Return
        ------
        string
            text containing nextRecordsUrl or '' if none
        """
        # create data file
        if 'nextRecordsUrl' in query:
            self.logger.debug("Fetching the next records at, %s",query['nextRecordsUrl'])
            nextRecordsUrl = query['nextRecordsUrl']
        else:
            nextRecordsUrl = ''

        return nextRecordsUrl

    def constructSelectStatement(self, fields):
        """Given an array of field names, constructs a valid Select statement

        Parameters
        -----------
        param: fields
            array of fields for select statement

        Return
        ------
        string
            Select statement
        """
        selectStatement = "SELECT "+",".join(fields)
        self.logger.debug("select statement, %s", selectStatement)
        return selectStatement
