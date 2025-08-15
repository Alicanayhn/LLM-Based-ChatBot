function logout() {
        localStorage.clear()
        window.location.href = "index.html"
}

function displayFileName() {
    const input = document.getElementById('file-upload');
    const fileNameDiv = document.getElementById('selected-file-name');

    if (input.files.length > 0) {
      fileNameDiv.textContent = "Seçilen dosya: " + input.files[0].name;
    } else {
      fileNameDiv.textContent = "Henüz dosya seçilmedi";
    }
}    

async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
      alert("Kullanıcı adı ve şifre gerekli.");
      return;
    }

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: {
          Auth: "Basic " + btoa(`${username}:${password}`),
        },
      });

      if (res.ok) {
        const data = await res.json();

        if (data.role === "admin") {
          window.location.href = "admin.html";
        } else {
          window.location.href = "chatbot.html";
        }
      } else {
        alert("Giriş başarısız. Kullanıcı adı veya şifre hatalı.");
      }
    } catch (error) {
      alert("Sunucuya ulaşılamıyor. Hata :"+ `${error}`);
    }
}

async function signup() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!username || !password) {
      alert("Kullanıcı adı ve şifre gerekli.");
      return;
    }

    try{
        const res = await fetch('/api/v1/auth/signup',{
        method: "POST",
        headers: {
            info: `${username}:${password}`,
            },
        });
        
        if(res.ok){
            const message = await res.json()
            alert(`${message.message}`)
        }
    }catch(error){
        return alert("Hata:" + `${error}`)
    }
}

async function upload_file() {
      const input_file = document.getElementById('file-upload');
      const file = input_file.files[0];

      const formData = new FormData();
      formData.append("file",file);
      
      try{
        const res = await fetch("/api/v1/users/files",{
          method: "POST",
          body: formData
        });

        if(res.ok){
          const result = await res.json()
          alert("Dosya Gönderimi başarılı: " + `${result.message}`)
        }else{
          const result = await res.json()
          alert("Dosya s3'e kaydedilemedi: " + `${result.error}`)
        }
      }catch(error){
        alert("Hata:" + `${error}`)
      }

}

async function list_buckets() {
    try {
      const res = await fetch('/api/v1/admin/list-buckets');
      const data = await res.json();
      const list = document.getElementById('fileList');
      list.innerHTML = '';
      data.files.forEach((file, i) => {
        const li = document.createElement('li');
        li.innerHTML = `
          <label>
            <input type="radio" name="file" value="${file}">
            ${file}
          </label>
        `;
        list.appendChild(li);
      });
    } catch(error) {
      alert(error);
    }
}

async function send_object_name() {
    const selected_file = document.querySelector("input[name='file']:checked"); 
    if(!selected_file){
      alert("Eğitim için bir dosya seçiniz!");
    }

    const file_name = selected_file.value

    const res = await fetch("/api/v1/admin/object-name",{
      method: "POST",
      headers: {
        "Content-type": "application/json"
      },
      body: JSON.stringify({object_name : file_name})
    })

    const message = await res.json()

    alert(`${message.message}`)
}

async function chatbot() {
    const prompt = document.getElementById('promptInput').value.trim();
    const responseBox = document.getElementById("responseBox");

    if (!prompt.trim()) {
      responseBox.style.display = "block";        
      responseBox.innerText = "Lütfen bir şeyler yaz.";
      return;
    }

    responseBox.style.display = "block";
    responseBox.innerText = "Yanıt bekleniyor...";

    const res = await fetch('/api/v1/users/chatbot',{
      method: 'POST',
      headers: {
        "Content-type": "application/json"
      },
      body: JSON.stringify({prompt : prompt})
    });

    const data = await res.json();
    responseBox.innerText = data.response || "Cevap alınamadı.";
}