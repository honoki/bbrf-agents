import boto3
import os
from bbrf.bbrf import BBRFClient

bbrf_conf = {
  "couchdb": os.environ['BBRF_COUCHDB_URL'],
  "username": os.environ['BBRF_USERNAME'],
  "password": os.environ['BBRF_PASSWORD'],
  "slack_token": os.environ['BBRF_SLACK_TOKEN'],
}

def bbrf(command):
    return BBRFClient(command, bbrf_conf).run()
    
# register all agents once at deploy time so you can use it across your workstations
# and set the agent gateway to the right AWS Gateway API Endpoint

def register_all(event, context):
    client = boto3.client('lambda', region_name='us-east-1')
    lambdas = client.list_functions()
    
    for l in lambdas['Functions']:
        if l['FunctionName'].endswith('-agent'):
            agent_name = l['FunctionName'].rsplit('-', 1)[0]
            # remove leading bbrf-agent-dev-
            agent_name = agent_name.replace(os.environ['LAMBDA_NAME_PREFIX'], '')
            print('Registering agent '+agent_name)
            bbrf('agent register '+agent_name)
            
    print('Setting agent endpoint to '+os.environ['ENDPOINT_URL'])
    bbrf('agent gateway '+os.environ['ENDPOINT_URL'])