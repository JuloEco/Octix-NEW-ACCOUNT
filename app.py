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
import time
import secrets
import requests
from flask import Flask, render_template_string, request, flash, url_for
from messages.envoi_message import envoyer_email_confirmation, envoyer_code_reinitialisation

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "octix_portal_secret")

OCTIX_URL = os.environ.get("OCTIX_URL", "http://localhost:5050")
OCTIX_INTERNAL_KEY = os.environ.get("OCTIX_INTERNAL_KEY")

from compte_routes import compte_bp
app.register_blueprint(compte_bp)

def _internal_headers():
    """Header attendu par octix.py sur /user/<username>/email et
    /reset-password. Doit être la même valeur des deux côtés."""
    return {"X-Internal-Key": OCTIX_INTERNAL_KEY} if OCTIX_INTERNAL_KEY else {}

APPS = [
    {"key": "opsiom", "name": "Opsiom", "tagline": "Recherche IA", "file": "opsiom.png"},
    {"key": "omnia", "name": "Omnia", "tagline": "Apprentissage du code", "file": "omnia.png"},
    {"key": "axiom", "name": "Axiom", "tagline": "Jeux vidéo", "file": "axiom.png"},
]


def octix_register(username, password, email, classroom_role):
    try:
        r = requests.post(
            f"{OCTIX_URL}/register",
            json={
                "username": username,
                "password": password,
                "email": email,
                "classroom_role": classroom_role,
            },
            timeout=15,
        )

        app.logger.info(
            "Octix /register -> HTTP %s : %s",
            r.status_code,
            r.text[:500]
        )

        # 1. Succès (200 OK ou 201 Created)
        if r.status_code in (200, 201):
            return True, None

        # 2. Cas spécifique : Utilisateur / Mail déjà existant
        if r.status_code == 409:
            return False, "Ce nom d'utilisateur ou cet e-mail est déjà utilisé."

        # 3. Autres erreurs renvoyées par l'API
        try:
            data = r.json()
            # Cherche 'error', 'message' ou 'detail'
            error = data.get("error") or data.get("message") or data.get("detail") or f"Erreur Octix HTTP {r.status_code}"
        except Exception:
            error = f"Erreur Octix HTTP {r.status_code}: {r.text[:200]}"

        return False, error

    except requests.exceptions.Timeout as e:
        app.logger.error("Timeout vers Octix API (%s/register): %r", OCTIX_URL, e)
        return False, "Octix met trop de temps à répondre. Réessaie dans quelques secondes."

    except requests.exceptions.ConnectionError as e:
        app.logger.error("Erreur de connexion vers Octix API (%s/register): %r", OCTIX_URL, e)
        return False, "Impossible de joindre le serveur Octix."

    except requests.exceptions.RequestException as e:
        app.logger.exception("Erreur HTTP vers Octix API (%s/register): %r", OCTIX_URL, e)
        return False, "Une erreur de communication avec Octix est survenue."


def octix_get_email(username):
    """Récupère l'e-mail associé à un pseudo. Nécessite un endpoint côté
    octix.py (voir CONTRAT_OCTIX_API.md). Retourne None si le compte
    n'existe pas ou si l'API est injoignable."""
    try:
        r = requests.get(f"{OCTIX_URL}/user/{username}/email", headers=_internal_headers(), timeout=5)
        if r.status_code == 200:
            return r.json().get("email")
        return None
    except requests.exceptions.RequestException:
        return None


def octix_reset_password(username, new_password):
    """Écrase le mot de passe d'un compte existant. Nécessite un endpoint
    côté octix.py (voir CONTRAT_OCTIX_API.md)."""
    try:
        r = requests.post(
            f"{OCTIX_URL}/reset-password",
            json={"username": username, "new_password": new_password},
            headers=_internal_headers(),
            timeout=5,
        )
        if r.status_code == 200:
            return True, None
        return False, r.json().get("error", "Erreur inconnue lors de la réinitialisation.")
    except requests.exceptions.RequestException:
        return False, "Octix est injoignable pour le moment. Réessaie dans un instant."


# --- Codes de réinitialisation en mémoire (à remplacer par un stockage
#     persistant type Redis/DB si le portail tourne sur plusieurs workers,
#     sinon un redémarrage ou un second worker perd les codes en cours). ---
RESET_CODES = {}
CODE_DUREE_VALIDITE = 10 * 60  # 10 minutes
TENTATIVES_MAX = 5


def generer_code():
    return f"{secrets.randbelow(1_000_000):06d}"


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
  .hint a{color:var(--accent); text-decoration:underline;}
  .radio-row{display:flex; gap:18px;}
  .radio-option{
    display:flex; align-items:center; gap:6px;
    font-size:0.9rem; font-family:'Inter', sans-serif; color:var(--text);
    cursor:pointer;
  }
  .radio-option input{width:auto; accent-color:var(--accent);}
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
        <p>Ton identifiant <b>{{ username }}</b> est prêt. Retourne sur Opsiom, Omnia ou Axiom et connecte-toi avec ce pseudo et ce mot de passe. Un e-mail de confirmation vient de t'être envoyé.</p>
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
          <label for="email">E-mail</label>
          <input type="email" id="email" name="email" placeholder="ton@email.com" required>
        </div>
        <p class="hint"><a href="{{ url_for('why_email') }}" target="_blank">Pourquoi on te le demande ?</a></p>
        <div class="field">
          <label>Profil Classroom</label>
          <div class="radio-row">
            <label class="radio-option">
              <input type="radio" name="classroom_role" value="eleve" required> Élève
            </label>
            <label class="radio-option">
              <input type="radio" name="classroom_role" value="prof" required> Professeur
            </label>
          </div>
        </div>
        <p class="hint">Détermine ce que tu verras en te connectant à Classroom.</p>
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

  <footer>Un seul identifiant Octix pour toute la famille d'apps Axiom. Ton mot de passe n'est jamais stocké en clair. <a href="{{ url_for('mot_de_passe_oublie') }}" style="color:var(--accent);">Mot de passe oublié ?</a></footer>

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
        email = request.form.get("email", "").strip()
        classroom_role = request.form.get("classroom_role", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not username or not email or not password or not classroom_role:
            flash("Merci de remplir le pseudo, l'e-mail, le profil Classroom et le mot de passe.")
            return render_template_string(PAGE, success=False, apps=APPS)

        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Cet e-mail ne semble pas valide.")
            return render_template_string(PAGE, success=False, apps=APPS)

        if classroom_role not in ("prof", "eleve"):
            flash("Merci de choisir Professeur ou Élève.")
            return render_template_string(PAGE, success=False, apps=APPS)

        if password != password2:
            flash("Les deux mots de passe ne correspondent pas.")
            return render_template_string(PAGE, success=False, apps=APPS)

        # Inscription Octix réussie
        ok, error = octix_register(username, password, email, classroom_role)
        if not ok:
            flash(error)
            return render_template_string(PAGE, success=False, apps=APPS)

        # Envoi de l'e-mail de confirmation avec suivi de retour
        succes_email, msg_email = envoyer_email_confirmation(email, username)
        if not succes_email:
            app.logger.error(f"[EMAIL] ÉCHEC pour {email} ({username}) -> {msg_email}")
        else:
            app.logger.info(f"[EMAIL] SUCCÈS pour {email} ({username})")

        return render_template_string(PAGE, success=True, username=username, apps=APPS)

    return render_template_string(PAGE, success=False, apps=APPS)


WHY_EMAIL_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pourquoi on te demande ton e-mail — Octix</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#060b12; --surface:#0d1620; --border:#1c2c3d;
    --primary:#0f7ba3; --accent:#4fc3de; --text:#eaf3f7; --text-muted:#7d95a8;
  }
  *{box-sizing:border-box;}
  body{
    margin:0; min-height:100vh;
    background: radial-gradient(circle at 50% -10%, rgba(15,123,163,0.28), transparent 55%), var(--bg);
    color:var(--text); font-family:'Inter', sans-serif;
    display:flex; justify-content:center; padding:64px 20px;
  }
  .wrap{max-width:520px;}
  .eyebrow{
    font-family:'JetBrains Mono', monospace; font-size:12px; letter-spacing:0.18em;
    text-transform:uppercase; color:var(--accent); margin:0 0 14px;
  }
  h1{font-family:'Space Grotesk', sans-serif; font-weight:600; font-size:1.8rem; margin:0 0 22px;}
  p{color:var(--text-muted); line-height:1.7; font-size:0.95rem; margin:0 0 18px;}
  p b{color:var(--text); font-weight:600;}
  .card{background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:28px 30px; margin-bottom:24px;}
  .back{display:inline-block; color:var(--accent); text-decoration:none; font-size:0.9rem; margin-top:8px;}
  .back:hover{text-decoration:underline;}
</style>
</head>
<body>
  <div class="wrap">
    <p class="eyebrow">Confidentialité</p>
    <h1>Pourquoi on te demande ton e-mail</h1>
    <div class="card">
      <p>Ton compte Octix ouvre les portes d'Opsiom, Omnia et Axiom — et cet écosystème continue de bouger : nouvelles fonctionnalités, mises à jour, parfois des changements qui touchent directement ton compte. L'e-mail est le seul canal qui nous permet de te prévenir même quand tu n'es pas en train d'utiliser une des apps.</p>
      <p><b>Ce que ça veut dire concrètement :</b> tu reçois un e-mail à la création de ton compte pour confirmer que tout est en ordre, et éventuellement un message ponctuel si quelque chose d'important change (sécurité, nouvelle app qui rejoint l'écosystème, etc.).</p>
      <p><b>Ce que ça ne veut pas dire :</b> pas de newsletter, pas de sollicitations marketing, pas de partage avec qui que ce soit en dehors d'Octix. Ton e-mail sert uniquement à te joindre au sujet de ton propre compte.</p>
    </div>
    <a class="back" href="{{ url_for('register') }}">&larr; Retour à la création de compte</a>
  </div>
</body>
</html>
"""


@app.route("/pourquoi-email")
def why_email():
    return render_template_string(WHY_EMAIL_PAGE)


FORGOT_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mot de passe oublié — Octix</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#060b12; --surface:#0d1620; --surface-2:#101b28; --border:#1c2c3d;
    --primary:#0f7ba3; --accent:#4fc3de; --text:#eaf3f7; --text-muted:#7d95a8; --danger:#e5636b;
  }
  *{box-sizing:border-box;}
  body{
    margin:0; min-height:100vh;
    background: radial-gradient(circle at 50% -10%, rgba(15,123,163,0.28), transparent 55%), var(--bg);
    color:var(--text); font-family:'Inter', sans-serif;
    display:flex; flex-direction:column; align-items:center; padding:64px 20px 40px;
  }
  .eyebrow{
    font-family:'JetBrains Mono', monospace; font-size:12px; letter-spacing:0.18em;
    text-transform:uppercase; color:var(--accent); margin:0 0 18px;
  }
  h1{font-family:'Space Grotesk', sans-serif; font-weight:600; font-size:1.9rem; text-align:center; margin:0 0 10px;}
  .subtitle{color:var(--text-muted); text-align:center; max-width:400px; line-height:1.55; margin:0 0 32px; font-size:0.92rem;}
  .card{width:100%; max-width:380px; background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:32px;}
  .field{display:flex; flex-direction:column; gap:6px; margin-bottom:16px;}
  .field label{font-size:12px; font-family:'JetBrains Mono', monospace; color:var(--text-muted); letter-spacing:0.04em;}
  .field input{
    background:var(--surface-2); border:1px solid var(--border); border-radius:9px;
    padding:12px 14px; color:var(--text); font-size:0.95rem; font-family:'Inter', sans-serif;
    outline:none; transition:border-color .15s ease;
  }
  .field input:focus{border-color:var(--accent);}
  .code-input{
    text-align:center; font-family:'JetBrains Mono', monospace;
    font-size:1.4rem; letter-spacing:0.5em; padding-left:0.5em;
  }
  .hint{font-size:12px; color:var(--text-muted); margin-top:-10px; margin-bottom:16px;}
  .error-box{
    background:rgba(229,99,107,0.1); border:1px solid rgba(229,99,107,0.35); color:#f3a1a6;
    border-radius:9px; padding:11px 14px; font-size:0.85rem; margin-bottom:18px;
  }
  button{
    width:100%; padding:13px; border:none; border-radius:9px;
    background:linear-gradient(135deg, var(--primary), var(--accent));
    color:#04141c; font-weight:600; font-size:0.95rem; font-family:'Inter', sans-serif;
    cursor:pointer; transition:opacity .15s ease;
  }
  button:hover{opacity:0.9;}
  .success{text-align:center; padding:6px 0 4px;}
  .success .check{
    width:48px; height:48px; border-radius:50%; background:rgba(79,195,222,0.15);
    border:1px solid rgba(79,195,222,0.4); display:flex; align-items:center; justify-content:center;
    margin:0 auto 18px; font-size:22px; color:var(--accent);
  }
  .success h2{font-family:'Space Grotesk', sans-serif; font-size:1.3rem; margin:0 0 10px;}
  .success p{color:var(--text-muted); font-size:0.9rem; line-height:1.6; margin:0;}
  .back{display:inline-block; color:var(--accent); text-decoration:none; font-size:0.85rem; margin-top:24px;}
  .back:hover{text-decoration:underline;}
</style>
</head>
<body>
  <p class="eyebrow">Identité Axiom</p>

  {% if step == 'request' %}
    <h1>Mot de passe oublié</h1>
    <p class="subtitle">Indique ton pseudo Octix : si le compte existe, on envoie un code à 6 chiffres à l'e-mail associé.</p>
    <div class="card">
      {% with messages = get_flashed_messages() %}
        {% if messages %}<div class="error-box">{{ messages[0] }}</div>{% endif %}
      {% endwith %}
      <form method="post" action="{{ url_for('mot_de_passe_oublie') }}">
        <div class="field">
          <label for="username">Pseudo</label>
          <input type="text" id="username" name="username" placeholder="Ton pseudo Octix" required>
        </div>
        <button type="submit">Envoyer le code</button>
      </form>
    </div>
  {% elif step == 'verify' %}
    <h1>Entre le code reçu</h1>
    <p class="subtitle">Un code à 6 chiffres vient d'être envoyé à l'e-mail associé à <b>{{ username }}</b>. Il expire dans 10 minutes.</p>
    <div class="card">
      {% with messages = get_flashed_messages() %}
        {% if messages %}<div class="error-box">{{ messages[0] }}</div>{% endif %}
      {% endwith %}
      <form method="post" action="{{ url_for('reinitialiser_mot_de_passe') }}" id="reset-form">
        <input type="hidden" name="username" value="{{ username }}">
        <div class="field">
          <label for="code">Code reçu par e-mail</label>
          <input type="text" id="code" name="code" class="code-input" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" placeholder="000000" required>
        </div>
        <div class="field">
          <label for="password">Nouveau mot de passe</label>
          <input type="password" id="password" name="password" placeholder="6 caractères minimum" required minlength="6">
        </div>
        <div class="field" style="margin-bottom:6px;">
          <label for="password2">Confirme le nouveau mot de passe</label>
          <input type="password" id="password2" name="password2" placeholder="Retape le même mot de passe" required minlength="6">
        </div>
        <p class="hint">Ce mot de passe remplacera l'ancien sur Opsiom, Omnia et Axiom.</p>
        <button type="submit">Réinitialiser mon mot de passe</button>
      </form>
    </div>
  {% else %}
    <h1>Terminé</h1>
    <div class="card">
      <div class="success">
        <div class="check">&#10003;</div>
        <h2>Mot de passe mis à jour</h2>
        <p>Ton nouveau mot de passe est actif dès maintenant sur Opsiom, Omnia et Axiom.</p>
      </div>
    </div>
  {% endif %}

  <a class="back" href="{{ url_for('register') }}">&larr; Retour à l'accueil</a>

{% if step == 'verify' %}
<script>
  const form = document.getElementById('reset-form');
  form.addEventListener('submit', function(e){
    const p1 = document.getElementById('password').value;
    const p2 = document.getElementById('password2').value;
    if (p1 !== p2) {
      e.preventDefault();
      alert("Les deux mots de passe ne correspondent pas.");
    }
  });
</script>
{% endif %}
</body>
</html>
"""


@app.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def mot_de_passe_oublie():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Merci d'indiquer un pseudo.")
            return render_template_string(FORGOT_PAGE, step="request")

        email = octix_get_email(username)
        if email:
            code = generer_code()
            RESET_CODES[username] = {
                "code": code,
                "expires_at": time.time() + CODE_DUREE_VALIDITE,
                "attempts": 0,
            }
            try:
                envoyer_code_reinitialisation(email, username, code)
            except Exception as e:
                app.logger.warning(f"Échec de l'envoi du code de réinitialisation à {email} : {e}")
        # On affiche le même écran que le compte existe ou non, pour ne pas
        # révéler quels pseudos sont enregistrés (protection contre l'énumération).
        return render_template_string(FORGOT_PAGE, step="verify", username=username)

    return render_template_string(FORGOT_PAGE, step="request")


@app.route("/reinitialiser-mot-de-passe", methods=["POST"])
def reinitialiser_mot_de_passe():
    username = request.form.get("username", "").strip()
    code = request.form.get("code", "").strip()
    password = request.form.get("password", "")
    password2 = request.form.get("password2", "")

    entry = RESET_CODES.get(username)

    if password != password2:
        flash("Les deux mots de passe ne correspondent pas.")
        return render_template_string(FORGOT_PAGE, step="verify", username=username)

    if not entry:
        flash("Ce code a expiré ou n'existe plus. Redemande un code.")
        return render_template_string(FORGOT_PAGE, step="request")

    if time.time() > entry["expires_at"]:
        del RESET_CODES[username]
        flash("Ce code a expiré. Redemande-en un nouveau.")
        return render_template_string(FORGOT_PAGE, step="request")

    if entry["attempts"] >= TENTATIVES_MAX:
        del RESET_CODES[username]
        flash("Trop de tentatives. Redemande un nouveau code.")
        return render_template_string(FORGOT_PAGE, step="request")

    if code != entry["code"]:
        entry["attempts"] += 1
        flash("Code incorrect.")
        return render_template_string(FORGOT_PAGE, step="verify", username=username)

    ok, error = octix_reset_password(username, password)
    del RESET_CODES[username]  # le code ne doit servir qu'une fois, succès ou non
    if not ok:
        flash(error)
        return render_template_string(FORGOT_PAGE, step="request")

    return render_template_string(FORGOT_PAGE, step="done")


if __name__ == "__main__":
    app.run(debug=True, port=5051)
