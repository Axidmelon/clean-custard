import os
import resend
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Resend client with your API key
resend.api_key = os.getenv("RESEND_API_KEY")

def send_verification_email(to_email: str, verification_link: str):
    """
    Sends a welcome and email verification email to a new user.
    """
    try:
        params = {
            "from": "onboarding@forgreco.com", 
            "to": [to_email],
            "subject": "Welcome to Custard! Please Verify Your Email",
            "html": f"""
                <h1>Welcome to Custard!</h1>
                <p>We're excited to have you on board.</p>
                <p>Please click the link below to verify your email address and get started:</p>
                <a href="{verification_link}">Verify My Email</a>
                <p>If you did not sign up for Custard, please ignore this email.</p>
            """,
        }

        email = resend.Emails.send(params)
        print(f"Verification email sent successfully: {email}")
        return email

    except Exception as e:
        print(f"Error sending verification email: {e}")
        return None

def send_password_reset_email(to_email: str, reset_link: str):
    """
    Sends a password reset email to a user.
    """
    try:
        params = {
            "from": "support@forgreco.com", # <-- Use a support address
            "to": [to_email],
            "subject": "Custard Account: Password Reset Request",
            "html": f"""
                <h1>Password Reset Request</h1>
                <p>We received a request to reset the password for your Custard account.</p>
                <p>Please click the link below to set a new password. This link will expire in 1 hour.</p>
                <a href="{reset_link}">Reset My Password</a>
                <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
            """,
        }
        email = resend.Emails.send(params)
        print(f"Password reset email sent successfully: {email}")
        return email
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return None