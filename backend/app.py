from flask import Flask,jsonify,request
from base64 import b64decode,b64encode
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import Column, Integer, String
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

fp16_mode = torch.cuda.is_available()

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

mlflow.set_tracking_uri("http://mlflow-server:5000")  
mlflow.set_experiment("distilgpt2-experiment")

try:
    engine = create_engine(DATABASE_URL)
    print('Baglanti basarili')
except Exception as e:
    print(f'Hata {e}')

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3_client = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

bucket_name = BUCKET_NAME

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer,primary_key=True)
    username = Column(String(50),unique=True)
    password = Column(String(50))
    role = Column(String(20))

def create_table():
        Base.metadata.create_all(engine)

@app.route('/api/v1/auth/login', methods=['POST'])
def basic_auth():
    
    auth_header = request.headers.get('Auth')

    print(auth_header)
    encoded = auth_header.split(' ')[1]
    print(encoded)
    decoded = b64decode(encoded).decode('utf-8')
    print(decoded)
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
    #print(username,password)
    try:
        db = SessionLocal()
        user = User(username=username,password=password,role='user')
        db.add(user)
        db.commit()
        db.close()
        return jsonify({'message':'Kullanıcı Eklendi'})
    except:
        return jsonify({'error':'Kullanıcı Eklenemedi'}), 400

@app.route('/api/v1/users/files',methods=["POST"])
def upload_file():
    
    file = request.files.get("file")
    try:
        s3_client.upload_fileobj(file,bucket_name,file.filename)
        print("S3' e kaydedildi")
        return jsonify({"message": "Dosya S3'e kaydedildi"})
    except:
        return jsonify({"error":"S3'e kaydedilemedi"}), 400

    
@app.route("/api/v1/admin/list-buckets", methods=["GET"])
def list_buckets():
    response = s3_client.list_objects_v2(Bucket=bucket_name)

    contents_keys = []

    for contents in response['Contents']:
        contents_keys.append(contents['Key'])
    
    return jsonify({"files": contents_keys})


def text_to_jsonl_dataset(metin, chunk_size=1024):
    import json
    chunks = [metin[i:i+chunk_size] for i in range(0, len(metin), chunk_size)]
    jsonl_list = []
    for chunk in chunks:
        item = {"prompt": chunk}
        json_line = json.dumps(item, ensure_ascii=False)
        jsonl_list.append(json_line)    
    print(f"[+] Dataset {len(chunks)} satır olarak RAM'de üretildi.")
    return jsonl_list


def prepare_dataset(dataset,tokenizer, max_length=1024):
    def tokenize_function(examples):
        tokens = tokenizer(
            examples["prompt"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens
    return dataset.map(tokenize_function, batched=True)

def load_distilgpt2_model(model_name="./distilbert/distilgpt2"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return model, tokenizer

def finetune(model, tokenizer, tokenized_dataset, output_dir="./distilgpt2-finetuned"):
    print("Fine Tuning Başlıyor")
    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,  
        num_train_epochs=3,
        logging_steps=10,
        save_steps=50,
        fp16=fp16_mode,                      
        save_total_limit=2,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_dataset,
        # eval_dataset=tokenized_dataset.select(range(0, 10)),
        tokenizer=tokenizer
    )

    with mlflow.start_run():
        trainer.train()

        # example_input = tokenizer("Merhaba!", return_tensors="np")["input_ids"]

        mlflow.pytorch.log_model(
            model,
            artifact_path="model", 
            registered_model_name="distilgpt2-chatbot"
        )

        mlflow.log_params({
            "epochs": 3,
            "batch_size": 2,
            "fp16": fp16_mode
        })

        # eval_result = trainer.evaluate()

        # for metric_name, metric_value in eval_result.items():
        #     if isinstance(metric_value, torch.Tensor):
        #         metric_value = metric_value.item()
        #     mlflow.log_metric(metric_name, metric_value)

        mlflow.log_metric("token_count", len(tokenized_dataset))

    # print(f"Model burada kaydedildi: {output_dir}")

finetune_status = {"status": "idle"}

def background_finetune(text):
    global finetune_status
    try:
        finetune_status["status"] = "running"
        json_list = text_to_jsonl_dataset(text)
        dataset_list = [json.loads(line) for line in json_list]
        dataset = Dataset.from_list(dataset_list)
        model, tokenizer = load_distilgpt2_model()
        tokenizer.pad_token = tokenizer.eos_token
        tokenized_dataset = prepare_dataset(dataset, tokenizer)
        finetune(model, tokenizer, tokenized_dataset)
        finetune_status["status"] = "done"
    except Exception as e:
        finetune_status["status"] = f"error: {str(e)}"



@app.route("/api/v1/admin/object-name", methods=["POST"])
def take_file():
    try:
        data = request.get_json()
        object_name = data.get('object_name')
        print("[*] İstek geldi, object_name:", object_name)
        
       
        pdf = s3_client.get_object(Bucket=bucket_name, Key=object_name)['Body']
        reader = PdfReader(BytesIO(pdf.read()))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        thread = threading.Thread(target=background_finetune, args=(text,))
        thread.start()
        # print("PDF'den metin çıkarıldı, toplam karakter:", len(text))
                
        # json_list = text_to_jsonl_dataset(text)
        # dataset_list = [json.loads(line) for line in json_list]
        # dataset = Dataset.from_list(dataset_list)
        # print("Dataset hazır, örnek:", dataset[0])

        # model, tokenizer = load_distilgpt2_model()
        # print("Model yüklendi")
        # tokenizer.pad_token = tokenizer.eos_token

        # tokenized_dataset = prepare_dataset(dataset, tokenizer)
        # print("Dataset tokenize edildi")
        
        # finetune(model, tokenizer, tokenized_dataset)
        # print("Fine-tune tamamlandı")

        return jsonify({'message': f'Fine tuning başlatıldı'})
    
    except Exception as e:
        return jsonify({"message": f"Hata: {str(e)}"}), 400
    
# def extract_text_from_pdf(pdf_path):
#     text = ""
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n"
#     return text

@app.route("/api/v1/admin/fine-tune-status", methods=["GET"])
def get_fine_tune_status():
    return jsonify(finetune_status)


MODEL_URI = "models:/distilgpt2-chatbot@prod"

model = mlflow.pytorch.load_model(MODEL_URI)
tokenizer = AutoTokenizer.from_pretrained("distilgpt2")

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
    create_table()
    app.run(host='0.0.0.0',port=5000)