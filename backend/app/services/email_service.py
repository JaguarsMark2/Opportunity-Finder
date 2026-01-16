"""Email service for sending transactional emails via SendGrid."""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from config import settings


class EmailService:
    """Service for sending transactional emails via SendGrid."""

    def __init__(self):
        """Initialize email service with SendGrid client."""
        self.client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.from_email = settings.SENDGRID_FROM_EMAIL

    def send_verification_email(self, to_email: str, verification_url: str) -> bool:
        """Send email verification link.

        Args:
            to_email: Recipient email address
            verification_url: Verification URL with token

        Returns:
            True if email sent successfully
        """
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="Verify Your Opportunity Finder Account",
            html_content=self._verification_html(verification_url)
        )
        try:
            response = self.client.send(message)
            return response.status_code == 202  # type: ignore[no-any-return]
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False

    def send_password_reset_email(self, to_email: str, reset_url: str) -> bool:
        """Send password reset link.

        Args:
            to_email: Recipient email address
            reset_url: Password reset URL with token

        Returns:
            True if email sent successfully
        """
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="Reset Your Opportunity Finder Password",
            html_content=self._reset_html(reset_url)
        )
        try:
            response = self.client.send(message)
            return response.status_code == 202  # type: ignore[no-any-return]
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False

    def _verification_html(self, verification_url: str) -> str:
        """Generate HTML for verification email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2>Verify Your Account</h2>
                <p>Thank you for registering with Opportunity Finder!</p>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_url}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
            </div>
        </body>
        </html>
        """

    def _reset_html(self, reset_url: str) -> str:
        """Generate HTML for password reset email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2>Reset Your Password</h2>
                <p>You requested to reset your password for Opportunity Finder.</p>
                <p>Click the link below to set a new password:</p>
                <p><a href="{reset_url}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
        </body>
        </html>
        """

    def send_welcome_email(self, to_email: str) -> bool:
        """Send welcome email after successful verification."""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="Welcome to Opportunity Finder!",
            html_content="""
            <h2>Welcome to Opportunity Finder!</h2>
            <p>Your email has been verified and your account is now active.</p>
            <p>You can now <a href="https://opportunityfinder.app/login">login</a> to start discovering validated opportunities.</p>
            """
        )
        try:
            response = self.client.send(message)
            return response.status_code == 202  # type: ignore[no-any-return]
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False
