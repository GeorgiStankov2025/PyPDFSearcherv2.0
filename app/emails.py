from fastapi import APIRouter
from fastapi_mail import FastMail,MessageSchema,ConnectionConfig
from starlette.responses import JSONResponse

from app.schemas import EmailSchema

router = APIRouter()

conf = ConnectionConfig(
    MAIL_USERNAME="bitproductions2024@gmail.com",
    MAIL_PASSWORD="unbv xvlo wrvs vgnm",  # Not your login password!
    MAIL_FROM="bitproductions2024@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,   # Modern replacement for MAIL_TLS
    MAIL_SSL_TLS=False,   # Modern replacement for MAIL_SSL
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@router.post("/emails", tags=["emails"])
async def send_mail(email: EmailSchema,verification_code:int):
    template = f"""
        <html>
        <body>


<p>Hi !!!
        <br>Thanks for registering to PyPDFSearcher! You may find your verification code from here {verification_code}.</p>


        </body>
        </html>
        """

    message = MessageSchema(
        subject="PyPDFSearcher team",
        recipients=email.model_dump().get("email"),  # List of recipients, as many as you can pass
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
