"""
Blueprint "Mon compte" du portail Octix.
==========================================
À greffer sur app.py (le portail) sans toucher au reste :

    from compte_routes import compte_bp
    app.register_blueprint(compte_bp)

Utilise la session Flask du portail (déjà configurée avec SECRET_KEY dans
app.py) pour garder l'utilisateur connecté entre deux pages : on y stocke
uniquement le token JWT et le pseudo, jamais le mot de passe.
"""

import os
import requests
from flask import Blueprint, render_template_string, request, session, redirect, url_for, flash

OCTIX_URL = os.environ.get("OCTIX_URL", "http://localhost:5050")

compte_bp = Blueprint("compte", __name__)


def _auth_headers():
    token = session.get("octix_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _octix_login(username, password):
    try:
        r = requests.post(f"{OCTIX_URL}/login", json={"username": username, "password": password}, timeout=5)
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("error", "Pseudo ou mot de passe incorrect.")
    except requests.exceptions.RequestException:
        return False, "Octix est injoignable pour le moment. Réessaie dans un instant."


def _octix_get(path):
    try:
        r = requests.get(f"{OCTIX_URL}{path}", headers=_auth_headers(), timeout=5)
        return r.status_code, (r.json() if r.content else {})
    except requests.exceptions.RequestException:
        return 503, {"error": "Octix est injoignable pour le moment."}


def _octix_put(path, payload):
    try:
        r = requests.put(f"{OCTIX_URL}{path}", json=payload, headers=_auth_headers(), timeout=5)
        return r.status_code, (r.json() if r.content else {})
    except requests.exceptions.RequestException:
        return 503, {"error": "Octix est injoignable pour le moment."}


def _octix_delete(path, payload):
    try:
        r = requests.delete(f"{OCTIX_URL}{path}", json=payload, headers=_auth_headers(), timeout=5)
        return r.status_code, (r.json() if r.content else {})
    except requests.exceptions.RequestException:
        return 503, {"error": "Octix est injoignable pour le moment."}


def login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "octix_token" not in session:
            return redirect(url_for("compte.connexion"))
        return view_func(*args, **kwargs)

    return wrapped


# --- Styles partagés (mêmes variables que le reste du portail) ---
BASE_STYLE = """
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
  .subtitle{color:var(--text-muted); text-align:center; max-width:420px; line-height:1.55; margin:0 0 32px; font-size:0.92rem;}
  .card{width:100%; max-width:420px; background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:28px 32px; margin-bottom:20px;}
  .card h2{font-family:'Space Grotesk', sans-serif; font-size:1.1rem; margin:0 0 18px; font-weight:600;}
  .field{display:flex; flex-direction:column; gap:6px; margin-bottom:14px;}
  .field label{font-size:12px; font-family:'JetBrains Mono', monospace; color:var(--text-muted); letter-spacing:0.04em;}
  .field input, .field select{
    background:var(--surface-2); border:1px solid var(--border); border-radius:9px;
    padding:11px 13px; color:var(--text); font-size:0.92rem; font-family:'Inter', sans-serif; outline:none;
  }
  .field input:focus, .field select:focus{border-color:var(--accent);}
  .row{display:flex; justify-content:space-between; padding:9px 0; border-bottom:1px solid var(--border-soft, #152233); font-size:0.9rem;}
  .row:last-child{border-bottom:none;}
  .row .label{color:var(--text-muted);}
  .row .value{color:var(--text); font-weight:500;}
  button{
    padding:12px 16px; border:none; border-radius:9px;
    background:linear-gradient(135deg, var(--primary), var(--accent));
    color:#04141c; font-weight:600; font-size:0.9rem; font-family:'Inter', sans-serif; cursor:pointer;
  }
  button:hover{opacity:0.9;}
  button.danger{background:linear-gradient(135deg, #a13840, var(--danger)); color:#fdf1f1;}
  .error-box{
    background:rgba(229,99,107,0.1); border:1px solid rgba(229,99,107,0.35); color:#f3a1a6;
    border-radius:9px; padding:11px 14px; font-size:0.85rem; margin-bottom:18px;
  }
  .success-box{
    background:rgba(79,195,222,0.1); border:1px solid rgba(79,195,222,0.35); color:#bfeaf3;
    border-radius:9px; padding:11px 14px; font-size:0.85rem; margin-bottom:18px;
  }
  .bar-track{width:100%; height:8px; background:var(--surface-2); border-radius:99px; overflow:hidden; margin-top:8px;}
  .bar-fill{height:100%; background:linear-gradient(90deg, var(--primary), var(--accent));}
  .back{display:inline-block; color:var(--accent); text-decoration:none; font-size:0.85rem; margin-top:8px;}
  .back:hover{text-decoration:underline;}
  .top-link{align-self:flex-end; max-width:420px; width:100%; margin-bottom:8px; text-align:right;}
  .top-link a{color:var(--text-muted); font-size:0.82rem; text-decoration:none;}
  .top-link a:hover{color:var(--accent);}
"""

LOGIN_PAGE = f"""
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Connexion — Octix</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{BASE_STYLE}</style></head><body>
  <p class="eyebrow">Identité Axiom</p>
  <h1>Connexion à ton compte</h1>
  <p class="subtitle">Utilise ton pseudo et ton mot de passe Octix (les mêmes que sur Opsiom, Omnia et Axiom).</p>
  <div class="card">
    {{% with messages = get_flashed_messages() %}}
      {{% if messages %}}<div class="error-box">{{{{ messages[0] }}}}</div>{{% endif %}}
    {{% endwith %}}
    <form method="post">
      <div class="field"><label for="username">Pseudo</label>
        <input type="text" id="username" name="username" required></div>
      <div class="field"><label for="password">Mot de passe</label>
        <input type="password" id="password" name="password" required></div>
      <button type="submit">Se connecter</button>
    </form>
    <p class="hint" style="margin-top:14px;"><a class="back" href="{{{{ url_for('mot_de_passe_oublie') }}}}">Mot de passe oublié ?</a></p>
  </div>
  <a class="back" href="{{{{ url_for('register') }}}}">&larr; Retour à l'accueil</a>
</body></html>
"""

COMPTE_PAGE = f"""
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mon compte — Octix</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{BASE_STYLE}</style></head><body>
  <div class="top-link"><a href="{{{{ url_for('compte.deconnexion') }}}}">Se déconnecter</a></div>
  <p class="eyebrow">Identité Axiom</p>
  <h1>Mon compte</h1>
  <p class="subtitle">Connecté en tant que <b style="color:var(--text);">{{{{ profil.username }}}}</b></p>

  {{% with messages = get_flashed_messages(with_categories=true) %}}
    {{% for category, message in messages %}}
      <div class="{{{{ 'success-box' if category == 'success' else 'error-box' }}}}" style="max-width:420px; width:100%;">{{{{ message }}}}</div>
    {{% endfor %}}
  {{% endwith %}}

  <div class="card">
    <h2>Profil</h2>
    <div class="row"><span class="label">Pseudo</span><span class="value">{{{{ profil.username }}}}</span></div>
    <div class="row"><span class="label">E-mail</span><span class="value">{{{{ profil.email }}}}</span></div>
    <div class="row"><span class="label">Membre depuis</span><span class="value">{{{{ profil.created_at[:10] if profil.created_at else '—' }}}}</span></div>
  </div>

  <div class="card">
    <h2>Profil Classroom</h2>
    <form method="post" action="{{{{ url_for('compte.changer_role') }}}}">
      <div class="field">
        <label for="classroom_role">Rôle</label>
        <select id="classroom_role" name="classroom_role">
          <option value="eleve" {{% if profil.classroom_role == 'eleve' %}}selected{{% endif %}}>Élève</option>
          <option value="prof" {{% if profil.classroom_role == 'prof' %}}selected{{% endif %}}>Professeur</option>
        </select>
      </div>
      <button type="submit">Mettre à jour</button>
    </form>
  </div>

  <div class="card">
    <h2>Progression LearnCode</h2>
    {{% if progress.has_progress %}}
      <div class="row"><span class="label">Niveau</span><span class="value">{{{{ progress.level }}}}</span></div>
      <div class="row"><span class="label">XP total</span><span class="value">{{{{ progress.xp }}}}</span></div>
      <div class="row"><span class="label">Cours notés</span><span class="value">{{{{ progress.cours_completes }}}}</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:{{{{ progress.progress_in_level }}}}%;"></div></div>
      <p style="font-size:0.78rem; color:var(--text-muted); margin:6px 0 0;">{{{{ progress.progress_in_level }}}} / {{{{ progress.next_level_xp }}}} XP avant le niveau {{{{ progress.level + 1 }}}}</p>
    {{% else %}}
      <p style="color:var(--text-muted); font-size:0.9rem; margin:0;">Pas encore de progression sur LearnCode — lance-toi sur un premier cours !</p>
    {{% endif %}}
  </div>

  <div class="card">
    <h2>Changer de mot de passe</h2>
    <form method="post" action="{{{{ url_for('compte.changer_mot_de_passe') }}}}">
      <div class="field"><label for="current_password">Mot de passe actuel</label>
        <input type="password" id="current_password" name="current_password" required></div>
      <div class="field"><label for="new_password">Nouveau mot de passe</label>
        <input type="password" id="new_password" name="new_password" required minlength="6"></div>
      <button type="submit">Changer le mot de passe</button>
    </form>
  </div>

  <div class="card" style="border-color:rgba(229,99,107,0.35);">
    <h2 style="color:var(--danger);">Zone de danger</h2>
    <p style="font-size:0.85rem; color:var(--text-muted); margin:0 0 16px;">Supprime définitivement ton compte Octix. Cette action ne peut pas être annulée. Tes données propres à chaque app (progression LearnCode, devoirs...) ne sont pas automatiquement supprimées par cette action.</p>
    <form method="post" action="{{{{ url_for('compte.supprimer_compte') }}}}" onsubmit="return confirm('Supprimer définitivement ton compte Octix ? Cette action est irréversible.');">
      <div class="field"><label for="password_delete">Confirme avec ton mot de passe</label>
        <input type="password" id="password_delete" name="password" required></div>
      <button type="submit" class="danger">Supprimer mon compte</button>
    </form>
  </div>

  <a class="back" href="{{{{ url_for('register') }}}}">&larr; Retour à l'accueil</a>
</body></html>
"""


@compte_bp.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ok, result = _octix_login(username, password)
        if not ok:
            flash(result)
            return render_template_string(LOGIN_PAGE)

        session["octix_token"] = result["token"]
        session["octix_username"] = result["username"]
        return redirect(url_for("compte.mon_compte"))

    return render_template_string(LOGIN_PAGE)


@compte_bp.route("/deconnexion")
def deconnexion():
    session.pop("octix_token", None)
    session.pop("octix_username", None)
    return redirect(url_for("compte.connexion"))


@compte_bp.route("/mon-compte")
@login_required
def mon_compte():
    status, profil = _octix_get("/account/me")
    if status == 401:
        session.pop("octix_token", None)
        flash("Ta session a expiré, reconnecte-toi.")
        return redirect(url_for("compte.connexion"))
    if status != 200:
        flash(profil.get("error", "Impossible de charger ton compte pour le moment."))
        return redirect(url_for("compte.connexion"))

    _, progress = _octix_get("/account/learncode-progress")

    return render_template_string(COMPTE_PAGE, profil=profil, progress=progress)


@compte_bp.route("/mon-compte/role", methods=["POST"])
@login_required
def changer_role():
    role = request.form.get("classroom_role", "")
    status, result = _octix_put("/account/classroom-role", {"classroom_role": role})
    if status == 200:
        flash("Profil Classroom mis à jour.", "success")
    else:
        flash(result.get("error", "Impossible de mettre à jour le profil Classroom."))
    return redirect(url_for("compte.mon_compte"))


@compte_bp.route("/mon-compte/mot-de-passe", methods=["POST"])
@login_required
def changer_mot_de_passe():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    status, result = _octix_put("/account/password", {
        "current_password": current_password,
        "new_password": new_password,
    })
    if status == 200:
        flash("Mot de passe changé avec succès.", "success")
    else:
        flash(result.get("error", "Impossible de changer le mot de passe."))
    return redirect(url_for("compte.mon_compte"))


@compte_bp.route("/mon-compte/supprimer", methods=["POST"])
@login_required
def supprimer_compte():
    password = request.form.get("password", "")
    status, result = _octix_delete("/account", {"password": password})
    if status == 200:
        session.pop("octix_token", None)
        session.pop("octix_username", None)
        flash("Ton compte Octix a été supprimé.", "success")
        return redirect(url_for("compte.connexion"))
    flash(result.get("error", "Impossible de supprimer le compte."))
    return redirect(url_for("compte.mon_compte"))
