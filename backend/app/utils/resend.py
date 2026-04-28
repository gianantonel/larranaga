import os
from typing import List
import resend
import logging

logger = logging.getLogger(__name__)

# Initialize Resend with API key from environment
resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(to: List[str], subject: str, html: str, text: str = None):
    """
    Send an email using Resend service.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject
        html: HTML content
        text: Plain text content (optional)
        
    Returns:
        dict: Resend API response
        
    Raises:
        Exception: If email sending fails
    """
    try:
        params = {
            "from": "Larrañaga <onboarding@resend.dev>",  # TODO: Change to verified domain
            "to": to,
            "subject": subject,
            "html": html,
        }
        
        if text:
            params["text"] = text
            
        email = resend.Emails.send(params)
        logger.info(f"Email sent to {to}: {email.get('id')}")
        return email
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}")
        raise e


def notify_admin_of_new_user(user_data: dict, admin_emails: List[str]):
    """
    Notify administrators about a new user registration requiring approval.
    
    Args:
        user_data: Dictionary containing user information (name, last_name, cuit, email)
        admin_emails: List of administrator email addresses to notify
    """
    subject = f"Nueva solicitud de acceso: {user_data['name']} {user_data['last_name']}"
    
    html = f"""
    <h2>Nueva solicitud de registro de usuario</h2>
    <p><strong>Nombre:</strong> {user_data['name']} {user_data['last_name']}</p>
    <p><strong>CUIT:</strong> {user_data.get('cuit', 'No proporcionado')}</p>
    <p><strong>Email:</strong> {user_data['email']}</p>
    <p><strong>Fecha de solicitud:</strong> {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <hr>
    <p>Por favor, revisa la solicitud en el panel de administración.</p>
    """
    
    try:
        send_email(admin_emails, subject, html)
    except Exception as e:
        logger.error(f"Failed to notify admins about new user: {str(e)}")
        raise e


def send_welcome_email(user_email: str, user_name: str, login_url: str = "/login"):
    """
    Send welcome email to a newly approved user.
    
    Args:
        user_email: User's email address
        user_name: User's first name
        login_url: URL for login page (default: /login)
    """
    subject = "¡Bienvenido a Larrañaga! Tu cuenta ha sido activada"
    
    html = f"""
    <h2>¡Hola {user_name}!</h2>
    <p>Nos complace informarte que tu solicitud de acceso ha sido aprobada y tu cuenta está ahora activa.</p>
    <p>Puedes iniciar sesión en la plataforma haciendo clic en el siguiente enlace:</p>
    <p><a href="{login_url}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Iniciar Sesión</a></p>
    <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
    <hr>
    <p><small>Este es un mensaje automático, por favor no responda a este correo.</small></p>
    """
    
    try:
        send_email([user_email], subject, html)
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")
        raise e