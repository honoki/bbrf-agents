import json
import requests
import boto3
from bbrf.bbrf import BBRFClient
import os

bbrf_conf = {
  "couchdb": os.environ['BBRF_COUCHDB_URL'],
  "username": os.environ['BBRF_USERNAME'],
  "password": os.environ['BBRF_PASSWORD'],
}

def bbrf(command):
    return BBRFClient(command, bbrf_conf).run()

'''
lambda-function dnsgrep-pool
'''
def pool(event, context):
    
    # get a list of all programs
    # and send each to run in a new lambda
    client = boto3.client('lambda', region_name='us-east-1')
    
    for program in bbrf('programs'):
        print('Executing dnsgrep-worker for '+program)
        client.invoke(FunctionName='bbrf-agents-dev-dnsgrep-worker', InvocationType='Event', Payload=json.dumps({'program': program}))

'''
lambda-function dnsgrep-worker
'''
def worker(event, context):
    
    # Parse parameters from query string:
    # e.g. curl https://urjuaodz1f.execute-api.us-east-1.amazonaws.com/dev/bbrf?program=name
    
    # when requested from API gateway
    if 'queryStringParameters' in event and event['queryStringParameters'] and 'program' in event['queryStringParameters']:
        program = event['queryStringParameters']['program']
    # when requested from lambda invoke
    elif 'program' in event:
        program = event['program']
    else:
        print(event)
        return {"statusCode":400, "body": "ERROR - program or task not found."}
    
    domains = []
    
    for scope in bbrf("scope in --wildcard --top -p "+program):
        print('Checking '+scope)
        results = execute(scope)
        print(results)
        for sub in results:
            domains.append(sub)
    
    print(domains)
    if len(domains) > 0:
        output = bbrf('domain add '+' '.join(domains)+' -p '+program + ' -s dnsgrep')
        print(output)
        return {"statusCode":200, "body": json.dumps(output)}
    
    return {"statusCode":204}

def execute(domain):
    r = requests.get('https://dns.bufferover.run/dns?q=.'+domain)
    results = []
    if r.json()['FDNS_A']:
        for domain in r.json()['FDNS_A']:
            results.append(domain.split(',')[1])
    if r.json()['RDNS']:
        for domain in r.json()['RDNS']:
            results.append(domain.split(',')[1])
#        results = [a.split(',')[1] for a in r.json()['FDNS_A']] + [a.split(',')[1] for a in r.json()['RDNS']]
    return results

if __name__ == "__main__":
    worker({}, {})