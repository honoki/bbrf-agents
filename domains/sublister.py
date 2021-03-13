import json
import requests
import boto3
import sublist3r
from bbrf.bbrf import BBRFClient
import os

MAX_PER_LAMBDA = 10

bbrf_conf = {
  "couchdb": os.environ['BBRF_COUCHDB_URL'],
  "username": os.environ['BBRF_USERNAME'],
  "password": os.environ['BBRF_PASSWORD'],
  "ignore_ssl_errors": os.environ['BBRF_IGNORE_SSL_ERRORS'],
}

def bbrf(command):
    return BBRFClient(command, bbrf_conf).run()

'''
lambda-function sublister-pool
'''
def pool(event, context):
    
    # get a list of all programs
    # and send each to run in a new lambda
        # i'm not sure this is a win for this script
    # but I wanna make sure this scales when
    # hundreds of programs exist
    client = boto3.client('lambda', region_name='us-east-1')
    
    for program in bbrf('programs'):
        print('Executing sublister-worker for '+program)
        client.invoke(FunctionName='bbrf-agents-dev-sublister-worker', InvocationType='Event', Payload=json.dumps({'program': program}))

'''
lambda-function sublister-worker
'''
def worker(event, context):
    
    # Parse parameters from query string:
    # e.g. curl https://urjuaodz1f.execute-api.us-east-1.amazonaws.com/dev/bbrf?program=vzm
    
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
    
    # If no scope was passed as the event, get the full scope
    if 'scope' in event:
        all_scope = event['scope']
    else:
        all_scope = bbrf("scope in --wildcard -p "+program)
        
    # If the scope is too large, invoke a new lambda
    # for separate chunks.
    if len(all_scope) > MAX_PER_LAMBDA:

        chunks = [all_scope[i:i + MAX_PER_LAMBDA] for i in range(0, len(all_scope), MAX_PER_LAMBDA)]
        client = boto3.client('lambda', region_name='us-east-1')
        for chunk in chunks:
            print('Executing sublister-worker for '+program+' with scope: '+','.join(chunk))
            client.invoke(FunctionName='bbrf-agents-dev-sublister-worker', InvocationType='Event', Payload=json.dumps({'program': program, 'scope':chunk}))
    # Otherwise let's get cracking
    else:
        for scope in all_scope:
            print('Checking '+scope)
            for sub in execute(scope):
                domains.append(sub)
    
    
    print(domains)
    if len(domains) > 0:
        output = bbrf('domain add '+' '.join(domains)+' -p '+program + ' -s sublister')
        return {"statusCode":200, "body": json.dumps(output)}
    
    return {"statusCode":204}

def execute(domain):
    results = sublist3r.main(domain, 20, None, [], False, False, False, None)
    return results

if __name__ == "__main__":
    print(execute('hackerone.com'))