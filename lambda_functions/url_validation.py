import json
import boto3
from datetime import datetime
from datetime import timedelta

# AWS LAMBDA CONFIGURATION
# Trigger: None
# Permissions: AWS CodePipeline
# Resource Policy: Invoke Lambda Function
# Public Function URL: HIDDEN - (HTTPS Endpoint)


def lambda_handler(event, context):
    
    #Grab information passed from event triggered
    decision = event['queryStringParameters']['value']
    code = event['queryStringParameters']['message']

    #Get client services 
    dynamodb = boto3.client('dynamodb')
    pipeline = boto3.client('codepipeline')

    current_time = datetime.now()
    current_time = current_time.strftime("%d/%m/%Y %H:%M:%S")
    current_time = datetime.strptime(current_time, "%d/%m/%Y %H:%M:%S")
    return_message = 'Invalid URL'

    #Read DB
    db_response = dynamodb.scan(
        TableName='POC'
    )

    print(db_response['Items'][0]['Accept_URL'])

    if decision == 'accept': #Accepted
        x = 0
        num_of_items = len(db_response['Items'])
        while x < num_of_items:
            if db_response['Items'][x]['Accept_URL']['S'] == code: #Correct token
                messageid = db_response['Items'][x]['message_id']['S']
                pipelinename = db_response['Items'][x]['Pipeline_name']['S']
                pipelinestagename = db_response['Items'][x]['Pipeline_stage']['S']
                pipelineaction = db_response['Items'][x]['Pipeline_action']['S']
                pipelinetoken = db_response['Items'][x]['Pipeline_token']['S']
                timestamp_old = db_response['Items'][x]['timestamp']['S']
                timestamp_old = datetime.strptime(timestamp_old, '%d/%m/%Y %H:%M:%S')
                expireson = timestamp_old + timedelta(hours=1)
                if current_time < expireson: # Not Expired
                    cp_response = pipeline.put_approval_result(
                       pipelineName=pipelinename,
                        stageName=pipelinestagename,
                        actionName=pipelineaction,
                        result={
                            'summary': 'CodePipeline requestion has been approved',
                            'status': 'Approved'
                        },
                    token=pipelinetoken
                    )
                    return_message = 'CodePipeline Approved'
                    #Delete Item from DB
                    dynamodb_delete_response = dynamodb.delete_item( 
                        TableName='POC',
                        Key={
                            'message_id' : {
                                'S' : messageid
                            }
                        }
                    )
                    break
                elif current_time > expireson:
                    dynamodb_delete_response = dynamodb.delete_item(
                        TableName='POC',
                        Key={
                            'message_id' : {
                                'S' : messageid
                            }
                        }
                    )
                    cp_response = pipeline.put_approval_result(
                        pipelineName=pipelinename,
                        stageName=pipelinestagename,
                        actionName=pipelineaction,
                        result={
                            'summary': 'CodePipeline request has been rejected due to expiration',
                            'status': 'Rejected'
                        },
                    token=pipelinetoken
                    )
                    return_message = 'URL Expired'
            x = x + 1
            
            
    elif decision == 'reject': #Rejected
        x = 0
        num_of_items = len(db_response['Items'])
        while x < num_of_items:
            if db_response['Items'][x]['Reject_URL']['S'] == code: #Still check Token
                messageid = db_response['Items'][x]['message_id']['S']
                pipelinename = db_response['Items'][x]['Pipeline_name']['S']
                pipelinestagename = db_response['Items'][x]['Pipeline_stage']['S']
                pipelineaction = db_response['Items'][x]['Pipeline_action']['S']
                pipelinetoken = db_response['Items'][x]['Pipeline_token']['S']
                timestamp_old = db_response['Items'][x]['timestamp']['S']
                timestamp_old = datetime.strptime(timestamp_old, '%d/%m/%Y %H:%M:%S')
                expireson = timestamp_old + timedelta(hours=1)
                if current_time < expireson:
                    cp_response = pipeline.put_approval_result(
                        pipelineName=pipelinename,
                        stageName=pipelinestagename,
                        actionName=pipelineaction,
                        result={
                            'summary': 'CodePipeline request has been rejected',
                            'status': 'Rejected'
                        },
                    token=pipelinetoken
                    )
                    return_message = 'CodePipeline Rejected'
                    dynamodb_delete_response = dynamodb.delete_item(
                        TableName='POC',
                        Key={
                            'message_id' : {
                                'S' : messageid
                            }
                        }
                    )
                    break
                elif current_time > expireson:
                    dynamodb_delete_response = dynamodb.delete_item(
                        TableName='POC',
                        Key={
                            'message_id' : {
                                'S' : messageid
                            }
                        }
                    )
                    cp_response = pipeline.put_approval_result(
                        pipelineName=pipelinename,
                        stageName=pipelinestagename,
                        actionName=pipelineaction,
                        result={
                            'summary': 'CodePipeline request has been rejected due to expiration',
                            'status': 'Rejected'
                        },
                    token=pipelinetoken
                    )
                    return_message = 'URL Expired'
            x = x + 1
    else:
        return_message = "Invalid URL"
        
    return {
        'statusCode': 200,
        'body': return_message
    }