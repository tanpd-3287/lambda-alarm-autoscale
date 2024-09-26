import boto3
import os
import json
import urllib3

# Initialize HTTP client for making API requests
http = urllib3.PoolManager()

# Get Slack Token and Channel ID from environment variables
slack_token = os.environ.get('SLACK_TOKEN')
slack_channel = os.environ.get('SLACK_CHANNEL')
slack_ids = os.environ.get('LIST_TO_SLACK', '').split(',')

# Lambda handler function
def lambda_handler(event, context):
    # Print the incoming event for debugging purposes
    print("Received event: ", json.dumps(event, indent=2))
    
    # SNS message containing the Auto Scaling event details
    sns_message = event['Records'][0]['Sns']['Message']
    message = json.loads(sns_message)
    
    # Extract necessary details from the Auto Scaling event
    service = message.get('Service', 'AWS Auto Scaling')
    time = message.get('Time')
    event_type = message.get('Event')
    ec2_instance_id = message.get('EC2InstanceId', 'N/A')
    autoscaling_group_name = message.get('AutoScalingGroupName', 'N/A')
    description = message.get('Description', 'No description provided')
    
    # Format Slack message to notify about the Auto Scaling event
    instance_details = f"- *EC2 Instance ID*: {ec2_instance_id}\n- *AutoScaling Group*: {autoscaling_group_name}\n- *Description*: {description}\n- *Event Time*: {time}"
    mention_text = ' '.join([f'<@{user_id}>' for user_id in slack_ids if user_id])
    
    slack_message = {
        "channel": slack_channel,
        "text": f"{mention_text}\n* :warning: Auto Scaling Event Detected:* {event_type}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{mention_text}\n* :warning: Auto Scaling Event Detected:* {event_type}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": instance_details
                }
            }
        ]
    }
    
    # Send the message to Slack using the Slack API (chat.postMessage)
    try:
        response = http.request(
            "POST",
            "https://slack.com/api/chat.postMessage",
            body=json.dumps(slack_message),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {slack_token}"
            }
        )
        
        # Check if the message was sent successfully
        response_data = json.loads(response.data.decode('utf-8'))
        if not response_data.get("ok"):
            print(f"Failed to send message to Slack: {response_data.get('error')}")
    except Exception as e:
        print(f"Error sending message to Slack: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent to Slack')
    }
