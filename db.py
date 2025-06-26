import boto3
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

users_table = dynamodb.Table(os.getenv("USERS_TABLE"))
appointments_table = dynamodb.Table(os.getenv("APPOINTMENTS_TABLE"))
notifications_table = dynamodb.Table(os.getenv("NOTIFICATIONS_TABLE"))
