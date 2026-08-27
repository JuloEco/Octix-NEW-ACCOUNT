"""
Octix Portal — le SEUL endroit où un compte Octix peut être créé.
====================================================================
Toutes les apps de l'écosystème (Opsiom, Omnia, Axiom...) redirigent ici
pour la création de compte. Elles ne font plus que du login contre l'API
Octix (octix.py) — jamais de /register en local.

Installation :
    pip install flask requests --break-system-packages

Lancement :
    python app.py
    -> portail disponible sur http://localhost:5051
    (nécessite que octix.py tourne sur http://localhost:5050, ou définis
     OCTIX_URL si l'API est ailleurs)
"""

import os
import requests
from flask import Flask, render_template_string, request, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "octix_portal_secret")

OCTIX_URL = os.environ.get("OCTIX_URL", "http://localhost:5050")

APPS = [
    {"key": "opsiom", "name": "Opsiom", "tagline": "Recherche IA", "file": "opsiom.png"},
    {"key": "omnia", "name": "Omnia", "tagline": "Apprentissage du code", "file": "omnia.png"},
    {"key": "axiom", "name": "Axiom", "tagline": "Jeux vidéo", "file": "axiom.png"},
]


def octix_register(username, password):
    try:
        r = requests.post(f"{OCTIX_URL}/register", json={"username": username, "password": password}, timeout=5)
        if r.status_code == 201:
            return True, None
        return False, r.json().get("error", "Erreur inconnue lors de la création du compte.")
    except requests.exceptions.RequestException:
        return False, "Octix est injoignable pour le moment. Réessaie dans un instant."


PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Octix — crée ton identifiant</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#060b12;
    --surface:#0d1620;
    --surface-2:#101b28;
    --border:#1c2c3d;
    --border-soft:#152233;
    --primary:#0f7ba3;
    --accent:#4fc3de;
    --text:#eaf3f7;
    --text-muted:#7d95a8;
    --danger:#e5636b;
  }
  *{box-sizing:border-box;}
  body{
    margin:0;
    min-height:100vh;
    background:
      radial-gradient(circle at 50% -10%, rgba(15,123,163,0.28), transparent 55%),
      var(--bg);
    color:var(--text);
    font-family:'Inter', sans-serif;
    display:flex;
    flex-direction:column;
    align-items:center;
    padding:64px 20px 40px;
  }
  .eyebrow{
    font-family:'JetBrains Mono', monospace;
    font-size:12px;
    letter-spacing:0.18em;
    text-transform:uppercase;
    color:var(--accent);
    margin:0 0 18px;
  }
  .logo-wrap{
    position:relative;
    width:120px;
    height:120px;
    margin-bottom:8px;
  }
  .logo-wrap::before{
    content:"";
    position:absolute;
    inset:-40px;
    background:radial-gradient(circle, rgba(79,195,222,0.35), transparent 65%);
    filter:blur(6px);
    z-index:0;
  }
  .logo-wrap img{
    position:relative;
    z-index:1;
    width:100%;
    height:100%;
    object-fit:contain;
  }
  h1{
    font-family:'Space Grotesk', sans-serif;
    font-weight:600;
    font-size:2.1rem;
    letter-spacing:-0.01em;
    text-align:center;
    margin:6px 0 10px;
  }
  .subtitle{
    color:var(--text-muted);
    text-align:center;
    max-width:420px;
    line-height:1.55;
    margin:0 0 40px;
    font-size:0.95rem;
  }
  .subtitle b{color:var(--text); font-weight:600;}
  .card{
    width:100%;
    max-width:380px;
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:16px;
    padding:32px;
  }
  .field{
    display:flex;
    flex-direction:column;
    gap:6px;
    margin-bottom:16px;
  }
  .field label{
    font-size:12px;
    font-family:'JetBrains Mono', monospace;
    color:var(--text-muted);
    letter-spacing:0.04em;
  }
  .field input{
    background:var(--surface-2);
    border:1px solid var(--border);
    border-radius:9px;
    padding:12px 14px;
    color:var(--text);
    font-size:0.95rem;
    font-family:'Inter', sans-serif;
    outline:none;
    transition:border-color .15s ease;
  }
  .field input:focus{border-color:var(--accent);}
  .hint{font-size:12px; color:var(--text-muted); margin-top:-10px; margin-bottom:16px;}
  .error-box{
    background:rgba(229,99,107,0.1);
    border:1px solid rgba(229,99,107,0.35);
    color:#f3a1a6;
    border-radius:9px;
    padding:11px 14px;
    font-size:0.85rem;
    margin-bottom:18px;
  }
  button{
    width:100%;
    padding:13px;
    border:none;
    border-radius:9px;
    background:linear-gradient(135deg, var(--primary), var(--accent));
    color:#04141c;
    font-weight:600;
    font-size:0.95rem;
    font-family:'Inter', sans-serif;
    cursor:pointer;
    transition:opacity .15s ease;
  }
  button:hover{opacity:0.9;}
  .success{
    text-align:center;
    padding:6px 0 4px;
  }
  .success .check{
    width:48px;
    height:48px;
    border-radius:50%;
    background:rgba(79,195,222,0.15);
    border:1px solid rgba(79,195,222,0.4);
    display:flex;
    align-items:center;
    justify-content:center;
    margin:0 auto 18px;
    font-size:22px;
    color:var(--accent);
  }
  .success h2{
    font-family:'Space Grotesk', sans-serif;
    font-size:1.3rem;
    margin:0 0 10px;
  }
  .success p{
    color:var(--text-muted);
    font-size:0.9rem;
    line-height:1.6;
    margin:0;
  }
  .success p b{color:var(--text);}

  .connected{
    margin-top:56px;
    width:100%;
    max-width:520px;
    text-align:center;
  }
  .connected .label{
    font-family:'JetBrains Mono', monospace;
    font-size:11px;
    letter-spacing:0.14em;
    text-transform:uppercase;
    color:var(--text-muted);
    margin-bottom:22px;
  }
  .threads{
    position:relative;
    height:34px;
    max-width:340px;
    margin:0 auto;
  }
  .apps-row{
    display:flex;
    justify-content:center;
    gap:28px;
    flex-wrap:wrap;
  }
  .app-badge{
    display:flex;
    flex-direction:column;
    align-items:center;
    width:104px;
  }
  .app-badge .icon{
    width:56px;
    height:56px;
    border-radius:14px;
    background:var(--surface);
    border:1px solid var(--border);
    display:flex;
    align-items:center;
    justify-content:center;
    margin-bottom:10px;
  }
  .app-badge .icon img{width:38px; height:38px; object-fit:contain;}
  .app-badge .name{font-size:0.85rem; font-weight:500;}
  .app-badge .tagline{font-size:0.72rem; color:var(--text-muted); margin-top:2px;}

  footer{
    margin-top:48px;
    font-size:0.78rem;
    color:var(--text-muted);
    text-align:center;
    max-width:380px;
    line-height:1.6;
  }
</style>
</head>
<body>

  <p class="eyebrow">Identité Axiom</p>
  <div class="logo-wrap">
    <img src="{{ url_for('static', filename='logos/octix.png') }}" alt="Octix">
  </div>
  <h1>Un compte. Toutes les apps.</h1>
  <p class="subtitle">Octix est l'identifiant unique de l'écosystème Axiom. <b>Crée-le une seule fois ici</b> : il fonctionnera directement sur Opsiom, Omnia et Axiom, avec le même pseudo et le même mot de passe.</p>

  <div class="card">
    {% if success %}
      <div class="success">
        <div class="check">&#10003;</div>
        <h2>Compte créé</h2>
        <p>Ton identifiant <b>{{ username }}</b> est prêt. Retourne sur Opsiom, Omnia ou Axiom et connecte-toi avec ce pseudo et ce mot de passe.</p>
      </div>
    {% else %}
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="error-box">{{ messages[0] }}</div>
        {% endif %}
      {% endwith %}
      <form method="post" id="octix-register-form">
        <div class="field">
          <label for="username">Pseudo</label>
          <input type="text" id="username" name="username" placeholder="Choisis un pseudo" required>
        </div>
        <div class="field">
          <label for="password">Mot de passe</label>
          <input type="password" id="password" name="password" placeholder="6 caractères minimum" required minlength="6">
        </div>
        <div class="field" style="margin-bottom:6px;">
          <label for="password2">Confirme le mot de passe</label>
          <input type="password" id="password2" name="password2" placeholder="Retape le même mot de passe" required minlength="6">
        </div>
        <p class="hint">Ce mot de passe sera le même partout : Opsiom, Omnia, Axiom.</p>
        <button type="submit">Créer mon compte Octix</button>
      </form>
    {% endif %}
  </div>

  <div class="connected">
    <p class="label">Fonctionne avec</p>
    <div class="apps-row">
      {% for a in apps %}
        <div class="app-badge">
          <div class="icon"><img src="{{ url_for('static', filename='logos/' + a.file) }}" alt="{{ a.name }}"></div>
          <div class="name">{{ a.name }}</div>
          <div class="tagline">{{ a.tagline }}</div>
        </div>
      {% endfor %}
    </div>
  </div>

  <footer>Un seul identifiant Octix pour toute la famille d'apps Axiom. Ton mot de passe n'est jamais stocké en clair.</footer>

<script>
  const form = document.getElementById('octix-register-form');
  if (form) {
    form.addEventListener('submit', function(e){
      const p1 = document.getElementById('password').value;
      const p2 = document.getElementById('password2').value;
      if (p1 !== p2) {
        e.preventDefault();
        alert("Les deux mots de passe ne correspondent pas.");
      }
    });
  }
</script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not username or not password:
            flash("Merci de remplir le pseudo et le mot de passe.")
            return render_template_string(PAGE, success=False, apps=APPS)

        if password != password2:
            flash("Les deux mots de passe ne correspondent pas.")
            return render_template_string(PAGE, success=False, apps=APPS)

        ok, error = octix_register(username, password)
        if not ok:
            flash(error)
            return render_template_string(PAGE, success=False, apps=APPS)

        return render_template_string(PAGE, success=True, username=username, apps=APPS)

    return render_template_string(PAGE, success=False, apps=APPS)


if __name__ == "__main__":
    app.run(debug=True, port=5051)
