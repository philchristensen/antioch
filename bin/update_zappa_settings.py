#!/usr/bin/env python

import json
import boto3

cfn = boto3.client('cloudformation')
paginator = cfn.get_paginator('describe_stacks')
pages = paginator.paginate(StackName="antioch-prod")
details = {}
for page in pages:
    for stack in page['Stacks']:
        for output in stack['Outputs']:
            details[output['OutputKey']] = output['OutputValue']

with(open('zappa_settings.json')) as f:
    cfg = json.loads(f.read())

cfg['prod']['vpc_config']['SecurityGroupIds'] = [details['WebappSecurityGroup']]
cfg['prod']['vpc_config']['SubnetIds'] = [
    details['PrivateSubnet1AID'],
    details['PrivateSubnet2AID'],
    details['PrivateSubnet3AID']
]
cfg['prod']['environment_variables']['DB_HOST'] = details['DatabaseHost']
cfg['prod']['environment_variables']['DB_PORT'] = details['DatabasePort']
cfg['prod']['environment_variables']['STATIC_BUCKET'] = details['StaticBucketName']

with(open('zappa_settings.json', 'w')) as f:
    f.write(json.dumps(cfg, indent=4))

print("Updated zappa_settings.json with stack variables.")