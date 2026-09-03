"""
Envoi de l'e-mail de bienvenue Octix.
=====================================
Appelé par app.py juste après la création réussie d'un compte, pour
prévenir le NOUVEL utilisateur que son compte est prêt.

Contient également un système de diagnostic pour identifier exactement
pourquoi un e-mail ne part pas sur Vercel ou en local.
"""

import smtplib
import os
import sys
import logging
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("octix_email")

BASE_DIR = Path(__file__).resolve().parent

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "octix.org@gmail.com"
HUB_URL = "https://omni-lbhc.onrender.com"


def verifier_configuration_email() -> tuple[bool, str]:
    """
    Vérifie toutes les préconditions requises pour l'envoi d'e-mail.
    Retourne (True, "OK") si tout est valide, sinon (False, "Raison de l'erreur").
    """
    # 1. Vérification de la clé d'environnement MDP
    app_password = os.environ.get("MDP")
    if not app_password:
        msg_err = "Variable d'environnement 'MDP' manquante ou vide dans l'environnement (Vercel/.env)."
        logger.error(f"[DIAGNOSTIC] ❌ {msg_err}")
        return False, msg_err
    
    # Sensibilité aux espaces dans le mot de passe d'application
    clean_mdp = app_password.replace(" ", "")
    if len(clean_mdp) != 16:
        logger.warning(
            f"[DIAGNOSTIC] ⚠️ La clé 'MDP' contient {len(clean_mdp)} caractères au lieu de 16. "
            "Assure-toi d'utiliser un Mot de passe d'application Google valide."
        )

    # 2. Vérification des fichiers d'assets requis
    html_path = BASE_DIR / "email_dark.html"
    logo_path = BASE_DIR / "octix.png"
    gif_path = BASE_DIR / "tick-dark-octix.gif"

    for path, nom in [(html_path, "email_dark.html"), (logo_path, "octix.png"), (gif_path, "tick-dark-octix.gif")]:
        if not path.is_file():
            msg_err = f"Fichier requis introuvable : {nom} (Chemin cherché : {path})"
            logger.error(f"[DIAGNOSTIC] ❌ {msg_err}")
            return False, msg_err

    logger.info("[DIAGNOSTIC] ✅ Toutes les préconditions locales (variables & fichiers) sont validées.")
    return True, "OK"


def envoyer_email_confirmation(destinataire: str, username: str) -> tuple[bool, str]:
    """
    Envoie l'e-mail 'ton compte Octix a été créé' à `destinataire`.
    Retourne (True, "Succès") ou (False, "Détail de l'erreur").
    """
    # Exécution préalable de la vérification
    valide, raison = verifier_configuration_email()
    if not valide:
        return False, f"Échec de pré-vérification : {raison}"

    app_password = os.environ.get("MDP").replace(" ", "")

    try:
        msg = EmailMessage()
        msg["Subject"] = "Ton compte Octix a été créé avec succès !"
        msg["From"] = SENDER_EMAIL
        msg["To"] = destinataire

        # Fallback Texte brut
        msg.set_content(
            f"Bienvenue {username} ! Ton compte Octix est prêt. "
            f"Accède à nos services ici : {HUB_URL}"
        )

        # 1. Traitement du template HTML
        with open(BASE_DIR / "email_dark.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        html = html.replace("{{USERNAME}}", username).replace("{{HUB_URL}}", HUB_URL)
        html_part = msg.add_alternative(html, subtype="html")

        # 2. Intégration des images CID
        with open(BASE_DIR / "octix.png", "rb") as f:
            html_part.add_related(f.read(), maintype="image", subtype="png", cid="<octix_logo.png>")

        with open(BASE_DIR / "tick-dark-octix.gif", "rb") as f:
            html_part.add_related(f.read(), maintype="image", subtype="gif", cid="<tick_dark_icon>")

        # 3. Authentification & Envoi SMTP avec capture fine des erreurs
        logger.info(f"Tentative d'envoi SMTP à {destinataire}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SENDER_EMAIL, app_password)
            server.send_message(msg)

        logger.info(f"✅ E-mail envoyé avec succès à {destinataire}")
        return True, "E-mail envoyé avec succès"

    except smtplib.SMTPAuthenticationError as e:
        err_msg = f"Erreur d'authentification Gmail SMTP (535) : Vérifie la clé 'MDP' sur Vercel. ({e})"
        logger.error(f"❌ {err_msg}")
        return False, err_msg

    except smtplib.SMTPException as e:
        err_msg = f"Erreur de protocole SMTP : {e}"
        logger.error(f"❌ {err_msg}")
        return False, err_msg

    except Exception as e:
        err_msg = f"Erreur inattendue lors de l'envoi de l'e-mail : {e}"
        logger.error(f"❌ {err_msg}", exc_info=True)
        return False, err_msg


if __name__ == "__main__":
    print("--- TEST ET DIAGNOSTIC EMAIL ---")
    
    if len(sys.argv) >= 3:
        destinataire_cli = sys.argv[1]
        username_cli = sys.argv[2]
        print(f"Lancement du test pour {destinataire_cli} ({username_cli})...")
        succes, message = envoyer_email_confirmation(destinataire_cli, username_cli)
        print(f"Résultat : {'RÉUSSI' if succes else 'ÉCHEC'} -> {message}")
    else:
        print("Lancement du contrôle de configuration seul...")
        ok, diag = verifier_configuration_email()
        if ok:
            print(" Configuration e-mail prête pour l'envoi !")
        else:
            print(f" Problème détecté : {diag}")
        print("\nUsage pour envoyer un mail de test : python envoi_message.py <destinataire> <username>")
