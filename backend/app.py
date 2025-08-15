from flask import Flask,jsonify,request
from base64 import b64decode,b64encode
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.automap import automap_base
import boto3
from io import BytesIO
from PyPDF2 import PdfReader
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset, Dataset
import json
from dotenv import load_dotenv
import torch
import mlflow
import mlflow.pytorch
import threading
import logging
import ModelTraining
import Preprocessing

load_dotenv()

fp16_mode = torch.cuda.is_available()

app = Flask(__name__)

logging.basicConfig(filename="app.log",filemode="a",format="%(asctime)s - %(levelname)s - %(message)s",level=logging.INFO)
logging.info("Ilk log tutuldu !")

DATABASE_URL = os.getenv('DATABASE_URL')
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI) 
mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

engine = create_engine(DATABASE_URL)

Base = automap_base()
Base.prepare(engine, reflect=True, schema="public")
User = Base.classes.users

SessionLocal = sessionmaker(bind=engine)

@app.route('/api/v1/auth/login', methods=['POST'])
def basic_auth():
    auth_header = request.headers.get('Auth')

    encoded = auth_header.split(' ')[1]

    decoded = b64decode(encoded).decode('utf-8')

    username,password = decoded.split(':',1)

    db = SessionLocal()
    user = db.query(User).filter_by(username=username,password=password).first()
    db.close()

    if user:
        return jsonify({'role': user.role})
    else:
        return jsonify({'error': 'Kullanıcı adı veya şifre hatalı'}), 401

@app.route('/api/v1/auth/signup', methods=['POST'])
def create_user():

    singup_header = request.headers.get('info')

    username,password = singup_header.split(':',1)

    try:
        db = SessionLocal()
        user = User(username=username,password=password,role='user')
        db.add(user)
        db.commit()
        db.close()
        return jsonify({'message':'Kullanıcı Eklendi'})
    except:
        return jsonify({'error':'Kullanıcı Eklenemedi'}), 400

@app.route('/api/v1/users/files',methods=["POST"]) # burası duzenlenecek user chatbot kullanacak
def upload_file():
    s3_client = boto3.client('s3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    file = request.files.get("file")

    try:
        s3_client.upload_fileobj(file,BUCKET_NAME,file.filename)
        print("S3' e kaydedildi")
        return jsonify({"message": "Dosya S3'e kaydedildi"})
    except:
        return jsonify({"error":"S3'e kaydedilemedi"}), 400

    
@app.route("/api/v1/admin/list-buckets", methods=["GET"])
def list_buckets():
    s3_client = boto3.client('s3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)

    contents_keys = []

    for contents in response['Contents']:
        contents_keys.append(contents['Key'])
    
    return jsonify({"files": contents_keys})

def background_finetune(text):
        
        json_list = Preprocessing.text_to_jsonl_dataset(text)
        dataset_list = [json.loads(line) for line in json_list]
        dataset = Dataset.from_list(dataset_list)
        model, tokenizer = ModelTraining.load_distilgpt2_model()
        tokenizer.pad_token = tokenizer.eos_token
        tokenized_dataset = Preprocessing.prepare_dataset(dataset, tokenizer)
        ModelTraining.finetune(model, tokenizer, tokenized_dataset)

@app.route("/api/v1/admin/object-name", methods=["POST"])
def take_file():
    s3_client = boto3.client('s3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    try:
        data = request.get_json()
        object_name = data.get('object_name')
        print("[*] İstek geldi, object_name:", object_name)
        
        pdf = s3_client.get_object(Bucket=BUCKET_NAME, Key=object_name)['Body']
        reader = PdfReader(BytesIO(pdf.read()))
        text = Preprocessing.pdf_to_text(reader)

        thread = threading.Thread(target=background_finetune, args=(text,))
        thread.start()

        return jsonify({'message': f'Fine tuning başlatıldı'})
    
    except Exception as e:
        return jsonify({"message": f"Hata: {str(e)}"}), 400

try:
    MODEL_URI = "models:/distilgpt2-chatbot@prod"

    model = mlflow.pytorch.load_model(MODEL_URI)
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
except Exception as e:
    print(f"Model download error: {e}")

@app.route("/api/v1/users/chatbot",methods=["POST"])
def chatbot():

    data = request.get_json()
    prompt_text = data.get("prompt")    

    if not prompt_text:
        return jsonify({"error": "Prompt alanı boş olamaz."}), 400

    input_ids = tokenizer(prompt_text, return_tensors="pt").input_ids
    output_ids = model.generate(input_ids, max_length=100, do_sample=True, top_k=50)
    response_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    return jsonify({
        "prompt": prompt_text,
        "response": response_text
    })

@app.route('/')
def index():
    return "Uygulama Index Html"

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000)