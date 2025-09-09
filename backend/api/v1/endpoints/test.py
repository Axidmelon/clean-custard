from fastapi import APIRouter, HTTPException
from core.email_service import send_verification_email

router = APIRouter()


@router.post("/test/send-email")
async def test_send_email(email_to: str):
    """
    A test endpoint to verify that the email service is working.
    """
    verification_link = "http://localhost:3000/auth/verify?token=fake-test-token"

    email_response = send_verification_email(to_email=email_to, verification_link=verification_link)

    if email_response is None:
        raise HTTPException(status_code=500, detail="Failed to send email.")

    return {"message": "Test email sent successfully!", "recipient": email_to}
