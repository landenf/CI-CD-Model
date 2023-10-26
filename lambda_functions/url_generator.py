import json
import boto3
import secrets
import os
from datetime import datetime

# AWS LAMBDA CONFIGURATION
# Trigger: SNS Topic (Pipeline Approval Topic)
# Permissions: AWS Cloudwatch Logs
# Resource Policy: Pipeline approval
# Enviorment Varibles: 'From Email', 'FunctionUrl' (Validation Function), 'To Email'

def lambda_handler(event, context):
    #Grab enviorment varibles
    validation_function_url = os.environ.get('FunctionalURL')
    to_email = os.environ.get('ToEmail')
    from_email = os.environ.get('FromEmail')

    #Grab varibles from SNS trigger event
    codepipeline_message = json.loads(event['Records'][0]['Sns']['Message'])
    pipelinename = codepipeline_message['approval']['pipelineName']

    print(codepipeline_message)

    #Generate Tokens
    accept_code = secrets.token_urlsafe()
    reject_code = secrets.token_urlsafe()
    
    print(accept_code)
    
    #Grab client services
    ses_client = boto3.client('ses')
    dynamodb = boto3.client('dynamodb')
    codepipeline = boto3.client('codepipeline')

    #Send Email to Stakeholders
    ses_message = "Hello, <br><br> The following Approval action is waiting for your response: <br><br> --Pipeline Details-- <br> Pipeline name: %s <br> Stage name: %s <br> Action name: %s <br> Region: %s <br><br> --Approval Details-- <br> Accept : %s?value=accept&message=%s <br> Reject : %s?value=reject&message=%s" % (pipelinename,codepipeline_message['approval']['stageName'],codepipeline_message['approval']['actionName'],codepipeline_message['region'],validation_function_url,accept_code,validation_function_url,reject_code)
    accept_response = ses_client.send_email(
        Source=from_email,
        Destination={
            'ToAddresses': [
                to_email,
            ]
        },
        Message={
            'Subject': {
                'Data': 'APPROVAL NEEDED: AWS CodePipeline %s for action Approval' %(pipelinename)
            },
            'Body': {
                'Text': {
                    'Data': ses_message
                },
                'Html': {
                    'Data': ses_message
                }
            }
        }
    )
    
    print(ses_message)
    print(accept_response)
    
    #Log time
    current_timestamp = datetime.now()
    current_timestamp = current_timestamp.strftime("%d/%m/%Y %H:%M:%S")
    
    #Create database entry with Tokens and Info
    data = dynamodb.put_item(
        TableName='POC', 
        Item={
            'message_id': {
                'S' : event['Records'][0]['Sns']['MessageId']
            },
            'timestamp': {
                'S' : current_timestamp
            },
            'Accept_URL': {
                'S' : accept_code
            },
            'Reject_URL': {
                'S' : reject_code
            },
            'Pipeline_name': {
                'S' : pipelinename
            },
            'Pipeline_stage': {
                'S' : codepipeline_message['approval']['stageName']
            },
            'Pipeline_action': {
                'S' : codepipeline_message['approval']['actionName']
            },
            'Pipeline_token': {
                'S' : codepipeline_message['approval']['token']
            }
        }
    )
    
    return {
        'statusCode': 200,
        'body': 'Email Sent Successfully'
    }