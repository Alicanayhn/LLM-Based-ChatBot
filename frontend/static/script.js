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
          window.location.href = "user.html";
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
            window.location.href = "index.html"
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