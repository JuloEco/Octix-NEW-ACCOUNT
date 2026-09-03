"""
Envoi des e-mails Octix (Bienvenue & Code de réinitialisation).
==============================================================
Intègre une gestion d'erreurs complète pour éviter tout plantage (HTTP 500)
sur Flask / Vercel.
"""

import smtplib
import os
import sys
import logging
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("octix_email")

BASE_DIR = Path(__file__).resolve().parent

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "octix.org@gmail.com"
HUB_URL = "https://omni-lbhc.onrender.com"


def _get_app_password() -> str:
    """Récupère et nettoie la clé MDP depuis les variables d'environnement."""
    raw_mdp = os.environ.get("MDP", "")
    return raw_mdp.replace(" ", "").strip()


def envoyer_email_confirmation(destinataire: str, username: str) -> tuple[bool, str]:
    app_password = _get_app_password()
    if not app_password:
        err = "Variable d'environnement 'MDP' manquante."
        logger.error(f"[EMAIL] {err}")
        return False, err

    try:
        msg = EmailMessage()
        msg["Subject"] = "Ton compte Octix a été créé avec succès !"
        msg["From"] = SENDER_EMAIL
        msg["To"] = destinataire

        # 1. Fallback texte brut obligatoire en premier
        msg.set_content(
            f"Bienvenue {username} ! Ton compte Octix est prêt.\n"
            f"Accède à nos services ici : {HUB_URL}"
        )

        # 2. Lecture du template HTML
        html_path = BASE_DIR / "email_dark.html"
        if not html_path.exists():
            return False, f"Fichier {html_path.name} introuvable."

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("{{USERNAME}}", username).replace("{{HUB_URL}}", HUB_URL)
        
        # 3. Ajout de la version HTML alternative
        msg.add_alternative(html, subtype="html")

        # 4. Ajout des images liées (add_related sur msg.get_payload(1))
        logo_path = BASE_DIR / "octix.png"
        gif_path = BASE_DIR / "tick-dark-octix.gif"

        # On cible le payload HTML (index 1)
        html_part = msg.get_payload(1)

        if logo_path.exists() and html_part:
            with open(logo_path, "rb") as f:
                html_part.add_related(f.read(), maintype="image", subtype="png", cid="<octix_logo.png>")

        if gif_path.exists() and html_part:
            with open(gif_path, "rb") as f:
                html_part.add_related(f.read(), maintype="image", subtype="gif", cid="<tick_dark_icon>")

        # 5. Envoi SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SENDER_EMAIL, app_password)
            server.send_message(msg)

        logger.info(f"[EMAIL] E-mail de confirmation envoyé à {destinataire}")
        return True, "E-mail envoyé avec succès"

    except Exception as e:
        err_msg = f"Échec d'envoi e-mail confirmation: {e}"
        logger.error(f"[EMAIL] {err_msg}")
        return False, err_msg

def envoyer_code_reinitialisation(destinataire: str, username: str, code: str) -> tuple[bool, str]:
    """
    Envoie le code de réinitialisation à `destinataire`.
    Retourne (True, "OK") ou (False, "Message d'erreur") sans planter.
    """
    app_password = _get_app_password()
    if not app_password:
        err = "Variable d'environnement 'MDP' manquante."
        logger.error(f"[EMAIL] {err}")
        return False, err

    try:
        msg = EmailMessage()
        msg["Subject"] = f"Ton code de réinitialisation Octix : {code}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = destinataire

        # Fallback texte
        msg.set_content(
            f"Bonjour {username},\n\n"
            f"Voici ton code de réinitialisation Octix : {code}\n"
            f"Il est valable 10 minutes. Si tu n'es pas à l'origine de cette demande, ignore cet e-mail."
        )

        # HTML
        html_path = BASE_DIR / "email_dark_code.html"
        if not html_path.exists():
            return False, f"Fichier {html_path.name} introuvable."

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("{{USERNAME}}", username).replace("{{CODE}}", code)
        
        html_part = msg.add_alternative(html, subtype="html")

        # Image CID
        logo_path = BASE_DIR / "octix.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                html_part.add_related(f.read(), maintype="image", subtype="png", cid="<octix_logo.png>")

        # Envoi SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SENDER_EMAIL, app_password)
            server.send_message(msg)

        logger.info(f"[EMAIL] Code de réinitialisation envoyé à {destinataire}")
        return True, "E-mail envoyé avec succès"

    except Exception as e:
        err_msg = f"Échec d'envoi code réinitialisation: {e}"
        logger.error(f"[EMAIL] {err_msg}")
        return False, err_msg


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "jules.ecorcheville@gmail.com"
    user = sys.argv[2] if len(sys.argv) > 2 else "TestUser"
    
    print(f"Test envoi e-mail vers {dest}...")
    ok, msg = envoyer_email_confirmation(dest, user)
    print(f"Résultat : {'SUCCÈS' if ok else 'ÉCHEC'} ({msg})")
