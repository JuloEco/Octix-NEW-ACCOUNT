"""
Envoi de l'e-mail de bienvenue Octix.
=====================================
Appelé par app.py juste après la création réussie d'un compte, pour
prévenir le NOUVEL utilisateur (pas une adresse en dur) que son compte
est prêt.

Peut aussi être lancé seul pour un test manuel :
    python envoi_message.py destinataire@example.com Pseudo
"""

import smtplib
import os
import sys
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "ecorcheville.jules@gmail.com"
APP_PASSWORD = os.environ["MDP"]

HUB_URL = "https://omni-lbhc.onrender.com"


def envoyer_email_confirmation(destinataire: str, username: str) -> None:
    """Envoie l'e-mail 'ton compte Octix a été créé' à `destinataire`."""
    msg = EmailMessage()
    msg["Subject"] = "Ton compte Octix a été créé avec succès !"
    msg["From"] = SENDER_EMAIL
    msg["To"] = destinataire

    msg.set_content(
        f"Bienvenue {username} ! Ton compte Octix est prêt. "
        f"Accède à nos services ici : {HUB_URL}"
    )

    # Chargement du gabarit HTML (email_dark.html) + remplacement des variables
    with open(BASE_DIR / "email_dark.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{USERNAME}}", username).replace("{{HUB_URL}}", HUB_URL)
    msg.add_alternative(html, subtype="html")

    # Intégration du logo Octix
    with open(BASE_DIR / "octix.png", "rb") as f:
        msg.get_payload()[1].add_related(f.read(), maintype="image", subtype="png", cid="<octix_logo.png>")

    # Intégration du GIF de validation
    with open(BASE_DIR / "tick-dark.gif", "rb") as f:
        msg.get_payload()[1].add_related(f.read(), maintype="image", subtype="gif", cid="<tick_dark_icon>")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)


def envoyer_code_reinitialisation(destinataire: str, username: str, code: str) -> None:
    """Envoie le code à 6 chiffres pour la réinitialisation du mot de passe."""
    msg = EmailMessage()
    msg["Subject"] = f"Ton code de réinitialisation Octix : {code}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = destinataire

    msg.set_content(
        f"Bonjour {username},\n\n"
        f"Voici ton code de réinitialisation Octix : {code}\n"
        f"Il est valable 10 minutes. Si tu n'es pas à l'origine de cette demande, ignore cet e-mail."
    )

    with open(BASE_DIR / "email_dark_code.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{USERNAME}}", username).replace("{{CODE}}", code)
    msg.add_alternative(html, subtype="html")

    with open(BASE_DIR / "octix.png", "rb") as f:
        msg.get_payload()[1].add_related(f.read(), maintype="image", subtype="png", cid="<octix_logo.png>")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)


if __name__ == "__main__":
    # Test manuel, sans passer par le formulaire :
    # python envoi_message.py destinataire@example.com Pseudo
    dest = sys.argv[1] if len(sys.argv) > 1 else "jules.ecorcheville@gmail.com"
    user = sys.argv[2] if len(sys.argv) > 2 else "TestUser"
    try:
        envoyer_email_confirmation(dest, user)
        print("E-mail envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi : {e}")
