import json
import requests
import random
from ratelimit import limits, sleep_and_retry
from bbrf.bbrf import BBRFClient
import os

VT_TOKEN = os.environ['VIRUSTOTAL_TOKEN']

bbrf_conf = {
  "couchdb": os.environ['BBRF_COUCHDB_URL'],
  "username": os.environ['BBRF_USERNAME'],
  "password": os.environ['BBRF_PASSWORD'],
  "ignore_ssl_errors": os.environ['BBRF_IGNORE_SSL_ERRORS'],
}

def bbrf(command):
    return BBRFClient(command, bbrf_conf).run()

'''
not implementing this as a pool event because of the rate limiting on the API
'''
def pool(event, context):
    pass

'''
lambda-function virustotal-worker
'''
def worker(event, context):
    
    # when requested from API gateway, get the program from the URL parameters
    if 'queryStringParameters' in event and event['queryStringParameters'] and 'program' in event['queryStringParameters']:
        program = event['queryStringParameters']['program']
    # when requested from Lambda invoke, get it from the event object
    elif 'program' in event:
        program = event['program']
    else:
        print(event)
        return {"statusCode": 400, "body": "ERROR - program not found."}
    
    output = []
    domains = []
    
    # randomize the scope list because it is likely this lambda
    # will time out - so give every subdomain a chance. :)
    scope = bbrf("scope in --wildcard --top -p "+program)
    random.shuffle(scope)
    print(scope)
    
    for domain in scope:
        domains = execute(domain)
        print(domains)
        if len(domains) > 0:
            bbrf('domain add '+' '.join(domains)+' -p '+program + ' -s virustotal')
    
    return {"statusCode": 200, "body": "done"}

@sleep_and_retry
@limits(calls=4, period=60)
def api_call(parameters):
    url = 'https://www.virustotal.com/vtapi/v2/domain/report'
    r = requests.get(url, params=parameters)

    if r.status_code != 200:
        raise Exception('API response: {}'.format(r.status_code))
    return r.json()

def execute(domain):
    results = []

    parameters = {'domain': domain, 'apikey': VT_TOKEN}
    response = api_call(parameters)
    
    if 'subdomains' not in response:
        return []
    for r in response['subdomains']:
        if not r in results:
            results.append(r)

    return results

if __name__ == "__main__":
    print(execute('hackerone.com'))