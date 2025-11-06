import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from database import create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str = Field(...)
    password: str = Field(...)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        # Try to import database module
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


def send_email_smtp(to_email: str, subject: str, body: str) -> Optional[str]:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM", user or "noreply@example.com")

    if not host or not user or not password:
        return "SMTP not configured"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.send_message(msg)
        return None
    except Exception as e:
        return str(e)


@app.post("/auth/login")
async def login(payload: LoginRequest, request: Request, user_agent: Optional[str] = Header(None)):
    # Basic validation (replace with real auth in production)
    if not payload.email or not payload.password:
        success = False
        message = "Email and password are required"
    else:
        success = True
        message = "Login success"

    # Gather context
    client_host = request.client.host if request.client else None
    ua = user_agent
    at = datetime.now(timezone.utc).isoformat()

    # Persist event
    try:
        create_document(
            "loginevent",
            {
                "email": payload.email,
                "success": success,
                "message": message,
                "ip": client_host,
                "user_agent": ua,
                "at": datetime.now(timezone.utc),
            },
        )
    except Exception as e:
        # Database unavailability shouldn't block login flow
        pass

    # Attempt email notification on successful login
    email_status = None
    if success:
        subject = "Login Notification"
        body = (
            f"Hallo,\n\nKami mendeteksi login ke akun Anda.\n\n"
            f"Email: {payload.email}\n"
            f"Waktu: {at}\n"
            f"IP: {client_host}\n"
            f"User-Agent: {ua}\n\n"
            f"Jika ini bukan Anda, segera ubah kata sandi Anda.\n"
        )
        email_status = send_email_smtp(payload.email, subject, body)

    if not success:
        return {"ok": False, "error": message}

    user = {"name": payload.email.split("@")[0] or "Pengguna", "email": payload.email}
    return {"ok": True, "user": user, "email_notification": "sent" if email_status is None else email_status or "skipped"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
