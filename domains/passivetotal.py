import json
import requests
import boto3
import random
from ratelimit import limits, sleep_and_retry
from bbrf.bbrf import BBRFClient
import os

PASSIVETOTAL_USERNAME = os.environ['PASSIVETOTAL_USER']
PASSIVETOTAL_KEY = os.environ['PASSIVETOTAL_KEY']

bbrf_conf = {
  "couchdb": os.environ['BBRF_COUCHDB_URL'],
  "username": os.environ['BBRF_USERNAME'],
  "password": os.environ['BBRF_PASSWORD'],
}

def bbrf(command):
    return BBRFClient(command, bbrf_conf).run()

'''
not implementing this as a pool event because of the rate limiting on the API
'''
def pool(event, context):
    pass

'''
lambda-function passivetotal-worker
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
    results = []
    
    # randomize the scope list because it is possible this lambda
    # will time out - so give every subdomain a chance. :)
    scope = bbrf("scope in --wildcard --top -p "+program)
    random.shuffle(scope)
    print(scope)
    
    for domain in scope:
        domains = execute(domain)
        print(domains)
        for d in domains:
            results.append(d)
    
    if len(results) > 0:
        bbrf('domain add '+' '.join(results)+' -p '+program + ' -s passivetotal')
    
    return {"statusCode": 200, "body": "done"}

@sleep_and_retry
@limits(calls=1, period=1)
def api_call(domain):
    url = 'https://api.passivetotal.org/v2/enrichment/subdomains'
    r = requests.get(url, params={'query': domain}, auth=(PASSIVETOTAL_USERNAME, PASSIVETOTAL_KEY))

    if r.status_code != 200:
        print('API response: {}'.format(r.status_code))
        return []
    return r.json()

def execute(domain):
    response = api_call(domain)
    
    if 'subdomains' not in response:
        return []
    return [x+'.'+domain for x in response['subdomains']]

if __name__ == "__main__":
    print(execute('hackerone.com'))