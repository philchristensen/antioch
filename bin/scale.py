#!/usr/bin/env python

import sys
import json
import boto3

def main(status):
    verb = 'Stopping' if status == 'down' else 'Starting'
    
    cfn = boto3.client('cloudformation')
    paginator = cfn.get_paginator('describe_stacks')
    pages = paginator.paginate(StackName="antioch-prod")
    details = {}
    for page in pages:
        for stack in page['Stacks']:
            for output in stack['Outputs']:
                details[output['OutputKey']] = output['OutputValue']

    print(f'{verb} ECS services...')
    ecs = boto3.client('ecs')
    ecs.update_service(
        cluster="antioch-prod",
        service=details['RedisServiceName'],
        desiredCount=int(status == 'up')
    )
    ecs.update_service(
        cluster="antioch-prod",
        service=details['BeatServiceName'],
        desiredCount=int(status == 'up')
    )
    ecs.update_service(
        cluster="antioch-prod",
        service=details['WorkerServiceName'],
        desiredCount=int(status == 'up')
    )
    
    print(f'{verb} RDS database...')
    rds = boto3.client('rds')
    if(status == 'down'):
        rds.stop_db_instance(DBInstanceIdentifier=details['DatabaseHost'].split('.')[0])
    else:
        rds.start_db_instance(DBInstanceIdentifier=details['DatabaseHost'].split('.')[0])
    
    print('Done.')

if(__name__ == '__main__'):
    main(sys.argv[1])