from flask import Flask,jsonify,request
from base64 import b64decode,b64encode
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import Column, Integer, String
import boto3
from io import BytesIO
from PyPDF2 import PdfReader
from dotenv import load_dotenv

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

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
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Hata message: {e}")

@app.route('/api/v1/auth/login', methods=['POST'])
def basic_auth():
    try:
        auth_header = request.headers.get('Auth')
    except Exception as e:
        print(f'Hata : {e}')

    try:
        print(auth_header)
        encoded = auth_header.split(' ')[1]
        print(encoded)
        decoded = b64decode(encoded).decode('utf-8')
        print(decoded)
        username,password = decoded.split(':',1)
    except Exception as e:
        return jsonify({'error': f'Hata : {e}'})

    db = SessionLocal()
    user = db.query(User).filter_by(username=username,password=password).first()
    db.close()

    if user:
        return jsonify({'role': user.role})
    else:
        return jsonify({'error': 'Kullanıcı adı veya şifre hatalı'}), 401

@app.route('/api/v1/auth/signup', methods=['POST'])
def create_user():
    try:
        singup_header = request.headers.get('info')
    except Exception as e:
        print(f'Hata : {e}')
        return jsonify({"error": "Header alınamadı"}), 400

    try:
        username,password = singup_header.split(':',1)
        print(username,password)
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"error": "username, password hatalı"}), 400
    
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
    try:
        file = request.files.get("file")
        try:
            s3_client.upload_fileobj(file,bucket_name,file.filename)
            print("S3' e kaydedildi")
            return jsonify({"message": "Dosya S3'e kaydedildi"})
        except:
            return jsonify({"error":"S3'e kaydedilemedi"}), 400
    except Exception as e:
        print(f"Dosya alınamadı, hata: {e}")
        return jsonify({"error":"Dosya Alınamadı"}), 400
    
@app.route("/api/v1/admin/list-buckets", methods=["GET"])
def list_buckets():
    response = s3_client.list_objects_v2(Bucket=bucket_name)

    contents_keys = []

    for contents in response['Contents']:
        contents_keys.append(contents['Key'])
    
    return jsonify({"files": contents_keys})

@app.route("/api/v1/admin/object-name",methods=["POST"])
def take_file():
    try:
        data = request.get_json()
        object_name = data.get('object_name')
        print(object_name)
        try:
            pdf = s3_client.get_object(Bucket=bucket_name,Key=object_name)['Body']
            reader = PdfReader(BytesIO(pdf.read()))

            for page in reader.pages:
                print(f"Text: {page.extract_text()}")
                
            return jsonify({"message":"pdf alındı"})
        except Exception as e:
            return jsonify({"message": f"pdf alınamadı, hata {e}"})
        # return jsonify({"message":"Object name alındı"})

    except:
        return jsonify({"message":"Object name alınamadı"})

@app.route('/')
def index():
    return "Uygulama Index Html"

if __name__ == "__main__":
    create_table()
    app.run(host='0.0.0.0',port=5000)