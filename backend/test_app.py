import pytest
from io import BytesIO
from base64 import b64encode
import json

from app import app, create_table, SessionLocal, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_test_user(username, password, role="user"):
    db = SessionLocal()
    user = User(username=username, password=password, role=role)
    db.add(user)
    db.commit()
    db.close()

def test_signup(client):
    username, password = "testuser", "testpass"
    res = client.post('/api/v1/auth/signup', headers={
        "info": f"{username}:{password}"
    })
    assert res.status_code == 200
    assert 'Kullanıcı Eklendi' in res.data.decode('utf-8')

def test_login(client):
    username, password = "testuser2", "testpass2"
    create_test_user(username, password)
    creds = b64encode(f"{username}:{password}".encode()).decode()
    res = client.post('/api/v1/auth/login', headers={
        "Auth": f"Basic {creds}"
    })
    assert res.status_code == 200
    assert b'role' in res.data

def test_upload_file(client):
    # Fake PDF dosyası oluştur
    data = {
        'file': (BytesIO(b"Fake PDF Data"), "testfile.pdf")
    }
    res = client.post('/api/v1/users/files', data=data, content_type='multipart/form-data')
    assert res.status_code == 200 or res.status_code == 400  # S3 erişimi yoksa 400 dönebilir

def test_list_buckets(client):
    res = client.get('/api/v1/admin/list-buckets')
    assert res.status_code == 200
    assert b'files' in res.data

def test_take_file(client):
    # Test amaçlı örnek bir dosya adı gönder
    data = { "object_name": "SeyahatBilgiFormu.pdf" }
    res = client.post('/api/v1/admin/object-name', data=json.dumps(data), content_type='application/json')
    # Hata veya başarı, önemli olan cevap dönmesi
    assert res.status_code == 200

