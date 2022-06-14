import boto3
import os

AWS_ACCESS_KEY_ID=os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.environ.get("AWS_SECRET_ACCESS_KEY")
region=os.environ.get("region")

client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=region
    )

def upload(filename, bucket):
    client.upload_file(filename, bucket, filename)

def download(filename, bucket):
    client.download_file(bucket, filename, filename)