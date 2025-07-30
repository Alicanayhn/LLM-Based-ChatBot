from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
from io import BytesIO
import boto3

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3_client = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

bucket_name = BUCKET_NAME

response = s3_client.list_objects_v2(Bucket=bucket_name)

for Contents in response['Contents']:
    print(Contents['Key'])

Contents = response['Contents']

print(Contents[0]['Key'])

key = Contents[0]['Key']
pdf = s3_client.get_object(Bucket=bucket_name,Key="CV Ali Can Ayhan #1.pdf (2).pdf")['Body']

reader = PdfReader(BytesIO(pdf.read()))

for page in reader.pages:
    print(f"Text: {page.extract_text()}")

print(type(pdf))