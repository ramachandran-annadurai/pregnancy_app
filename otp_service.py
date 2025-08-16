# File: otp_service.py
import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_otp(email: str) -> str | None:
    """
    Generates a 6-digit OTP and sends it to the specified email address using Gmail.
    """
    # Generate OTP using the user's method
    otp = ""
    for i in range(6):
        otp += str(random.randint(0, 9))
    
    # Get Gmail configuration from environment variables
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    # Check if environment variables are set
    if not sender_email or not sender_password:
        print("❌ Error: SENDER_EMAIL and SENDER_PASSWORD must be set in .env file")
        print("📧 OTP displayed in console for testing purposes")
        
        # Fallback: display in console
        print("\n" + "="*50)
        print("🔐 OTP VERIFICATION")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"🔢 Your OTP Code: {otp}")
        print("="*50)
        print("💡 OTP displayed in console due to missing .env configuration.")
        print("   Please create a .env file with SENDER_EMAIL and SENDER_PASSWORD")
        print("="*50 + "\n")
        
        return otp
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Your Patient Alert System Verification Code"
        
        body = f"""
        Hello!
        
        Your verification OTP is: {otp}
        
        Please enter this code to complete your registration.
        
        Best regards,
        Patient Alert System Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        
        print(f"✅ OTP sent successfully to {email}")
        return otp
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print("📧 OTP displayed in console for testing purposes")
        
        # Fallback: display in console
        print("\n" + "="*50)
        print("🔐 OTP VERIFICATION")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"🔢 Your OTP Code: {otp}")
        print("="*50)
        print("💡 OTP displayed in console due to email sending failure.")
        print("="*50 + "\n")
        
        return otp

def verify_otp(user_input: str, expected_otp: str) -> bool:
    """
    Verifies if the user input matches the expected OTP.
    """
    return user_input.strip() == expected_otp.strip()