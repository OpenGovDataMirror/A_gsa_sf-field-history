import os, csv, json, logging, datetime

class FieldHistoryFileWriter:
    path = ''

    def __init__(self, sfUrl, objectName, filePath=''):
        self.path = filePath+'data/'+sfUrl+'/'+datetime.datetime.now().strftime('%Y%m%d')+'/'+objectName+'_'+datetime.datetime.now().strftime('%Y%m%d-%H%M.%S')+'.csv'
        self.logger = logging.getLogger(__name__)
        self.logger.debug('%s initiated',__name__)
        self.logger.debug('New file created at, %s', self.path)

        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))

    def constructHeaderFields(self, fields):
        headerFields = json.loads("""{"records":[
                {"Id":"Id",
                "ParentId":"ParentId",
                "OldValue":"OldValue",
                "NewValue":"NewValue",
                "Field":"Field",
                "CreatedById":"CreatedById",
                "CreatedDate":"CreatedDate",
                "attributes": {
                    "url":"url",
                    "type": "type"
                },
                "IsDeleted":"IsDeleted"}]}""")
        # Core Salesforce objects do not use ParentId but instead AccountId or ContactId. To accommodate this, we mus change the list
        if "ParentId" not in fields:
            altField = self.getAltParentId(fields)
            # drop ParentId from the object
            headerFields["records"][0].pop("ParentId")
            # add the new key to the list
            headerFields["records"][0].update({altField[0]:altField[0]})
        return headerFields

    def writeFile(self, fields):
        """Writes field history data to file

        Parameters
        ----------
        input : json object in the format of the query endpoint (https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_query.htm)

            ex:
            {
              "records" : [{
                'Id': '017r00000471xrmAAA',
                'OldValue': 'blah',
                'NewValue': 'bleh',
                'Field': 'Name',
                'ParentId': '500234242342abc',
                'CreatedById': '001ao09u0913aaaa',
                'CreatedDate': '2018-12-18T18:49:40.000+0000',
                'IsDeleted': false,
                'attributes': {
                    'url': '/services/data/v32.0/sobjects/AccountHistory/017r00000471xroAAA',
                    'type': 'AccountHistory'
                }
              }]
            }
        """
        f=csv.writer(open(self.path,'a'))

        try:
            if len(fields['records']) > 0:
                parentId = "ParentId"
                if "ParentId" not in fields['records'][0]:
                    parentId = self.getAltParentId(fields['records'][0])[0]
                    self.logger.debug('ParentID Changed to %s', parentId)

                for item in fields['records']:
                    self.logger.debug("ITEMS LIST %s", item)
                    f.writerow([item['Id'],item['OldValue'],item['NewValue'], item['Field'], item['CreatedById'], item['CreatedDate'],item['attributes']['url'],item['attributes']['type'],item['IsDeleted'],item[parentId]])
        except Exception as e:
            self.logger.warning(e)
            self.logger.warning('Input does not match what was expected: %s', fields)

    def getAltParentId(self, fields):
        self.logger.debug("getAltParentId Fields: %s", fields)
        typicalFieldList = ['Id', 'ParentId', 'IsDeleted', 'CreatedById', 'CreatedDate', 'Field', 'OldValue', 'NewValue', 'attributes']

        # finds the difference between the two lists
        newFields = list(set(fields) - set(typicalFieldList))
        return newFields
