import requests, os, csv, datetime, json, sys, argparse, logging, logging.config, time
from requests.auth import HTTPBasicAuth
from FieldHistoryFileWriter import FieldHistoryFileWriter
from SalesforceApi import SalesforceApi

sfEnv = {}
# set initial logging levels
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description='Salesforce Field History Retrieval\n\nThis python script will authenticate against Salesforce and pull json responses containing field history data. Request responses are logged in the /logs directory. Each run of this app will generate multiple requests, those requests are merged into a single log file')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('orgName', nargs='?', default='', help='enter the org key of the environment contained in .env')
parser.add_argument('-d', '--debug', help='Prints detailed output to the /logs folder', action='store_true')
group.add_argument('-e', '--env', help='display list of Salesforce environments contained in the .env file', action='store_true')


args = parser.parse_args()

if args.orgName != '':
    with open('.env') as json_data:
        d = json.load(json_data)
    sfEnv = d[args.orgName]
    logger.info('Fetching history from, %s. Data will be stored in data/%s', args.orgName, sfEnv['salesforceURL'])

if args.debug:
    logStorageLocation = 'logs/'+datetime.datetime.now().strftime('%Y%m%d-%H%M.%S')+'.log'
    logger.info('Debug has been turned on, logs will be stored at %s', logStorageLocation)
    # make sure /log folder exists
    if not os.path.exists(os.path.dirname('logs/')):
        os.makedirs(os.path.dirname('logs/'))

    # you cannot update basicConfig but instead must overwrite existing logging config
    logger = logging.getLogger()
    fileh = logging.FileHandler(logStorageLocation, 'a')
    formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    fileh.setFormatter(formatter)
    log = logging.getLogger()  # root logger
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)
    log.addHandler(fileh)
    logger.info('Fetching history from, %s', sfEnv['salesforceURL'])
    logger.info('Logging turned on. File can be found at, %s',logStorageLocation)

if args.env:
    with open('.env') as json_data:
        d = json.load(json_data)
    if len(d) == 0:
        logging.info('No environments stored. Add credentials to the .env file. See .sample.env.')
    else:
        logging.info('The following environments have credentials stored: ')
        for item in d:
            logging.info('    - '+item)
        logging.info('You can use one of the sites by entering:\n\n  $ python retrieveHistory.py orgname\n')
    sys.exit()

# Instantiate the SalesforceApi
sa = SalesforceApi(environment=sfEnv)

sa.authenticate()
time.sleep(1)

# retrieve objects
response = sa.getObjects()

# filter response, return all History objects
historyObjects = sa.getHistoryObjects(response)

# for each history object, run the following pattern
for h in historyObjects:
    logger.info('Processing: '+h.name)
    # create file for storage
    fw = FieldHistoryFileWriter(sfUrl=sa.sfURL,objectName=h.name)
    headerFields = fw.constructHeaderFields(h.fields)
    fw.writeFile(headerFields)
    # query
    queryOutput = sa.query(h.fields,h.name)
    # write output to csv
    fw.writeFile(queryOutput)

    # fetch nextRecordsUrl
    nextRecordsUrl = sa.hasNextRecords(queryOutput)
    while nextRecordsUrl != '':
        # query
        output = sa.getNextRecords(nextRecordsUrl)
        fw.writeFile(output)
        nextRecordsUrl = sa.hasNextRecords(output)

logging.shutdown()
