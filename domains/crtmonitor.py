import json
import boto3
import psycopg2
import os
from bbrf.bbrf import BBRFClient
import asyncio
import functools

bbrf_conf = {
  "couchdb": os.environ['BBRF_COUCHDB_URL'],
  "username": os.environ['BBRF_USERNAME'],
  "password": os.environ['BBRF_PASSWORD'],
  "ignore_ssl_errors": os.environ['BBRF_IGNORE_SSL_ERRORS'] if 'BBRF_IGNORE_SSL_ERRORS' in os.environ else False,
}

def bbrf(command):
    return BBRFClient(command, bbrf_conf).run()

'''
lambda-function crtmonitor-pool
'''
def pool(event, context):
    
    # get a list of all programs
    # and send each to run in a new lambda
    # todo: this will require threading to process all 
    # lambda invocations at the same time, rather than
    # sequentially, which now causes the lambda to time out
    # after ~126 worker invocations
    client = boto3.client('lambda', region_name='us-east-1')
   
    loop = asyncio.new_event_loop()
    programs = bbrf('programs')
    print(programs)
    asyncio.gather(
        *[
            loop.run_in_executor(None, functools.partial(
                client.invoke,
                FunctionName='bbrf-agents-dev-crtmonitor-worker',
                InvocationType='Event',
                Payload=json.dumps({'program': program})
            ))
            for program in programs
        ]
    )

'''
lambda-function crtmonitor-worker
'''
def worker(event, context):
    
    # Parse parameters from query string:
    # e.g. curl https://urjuaodz1f.execute-api.us-east-1.amazonaws.com/dev/crtmonitor?program=name
    
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
    
    scope = bbrf("scope in --wildcard --top -p "+program)
    results = execute(scope)
    
    print(results)
    if len(results) > 0:
        output = bbrf('domain add '+' '.join(results)+' -p '+program + ' -s crtmonitor')
        return {"statusCode":200, "body": json.dumps(output)}
    
    return {"statusCode":204} # nothing added

def execute(domains):
    results = []
    conn = None
    try:
        conn = psycopg2.connect(host="crt.sh", database="certwatch", user="guest")
        conn.set_session(autocommit=True)
        cur = conn.cursor()
#        query = "SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%."+domain+"'));"
        query = "SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND ("
        for domain in domains:
            query = query + "reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%."+domain+"')) OR "
        query = query[:-4] + ")"
        cur.execute(query)
        row = cur.fetchone()
        while row is not None:
            results.append(row[0])
            row = cur.fetchone()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            
    return list(set(results))  # remove duplicates for efficiency! e.g. for paypal this reduces from ~15k domains to ~4k

if __name__ == "__main__":
    pool({}, {})