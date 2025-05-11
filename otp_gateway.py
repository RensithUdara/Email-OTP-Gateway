from flask import Flask, request, jsonify
import random
import smtplib
from email.message import EmailMessage
import time
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = Flask(__name__)

# In-memory OTP store: {email: (otp, timestamp)}
otp_store = {}

# Configuration from .env
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
OTP_EXPIRY_SECONDS = 300  # 5 minutes

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    msg = EmailMessage()
    
    # Plain text fallback
    msg.set_content(f"Your OTP code is: {otp}")

    # HTML content
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f2f2f2; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          <h2 style="color: #333;">Your OTP Code</h2>
          <p style="font-size: 16px; color: #555;">Use the following code to verify your email:</p>
          <h1 style="color: #007bff; font-size: 36px; letter-spacing: 2px;">{otp}</h1>
          <p style="color: #888;">This code is valid for 5 minutes. Do not share it with anyone.</p>
        </div>
      </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')

    msg['Subject'] = '🔐 Your OTP Verification Code'
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    otp = generate_otp()
    timestamp = int(time.time())

    try:
        send_otp_email(email, otp)
        otp_store[email] = (otp, timestamp)
        return jsonify({"message": "OTP sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    user_otp = data.get("otp")

    if not email or not user_otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    record = otp_store.get(email)

    if not record:
        return jsonify({"error": "No OTP found for this email"}), 404

    stored_otp, timestamp = record
    current_time = int(time.time())

    if current_time - timestamp > OTP_EXPIRY_SECONDS:
        del otp_store[email]
        return jsonify({"error": "OTP expired"}), 400

    if user_otp != stored_otp:
        return jsonify({"error": "Invalid OTP"}), 401

    del otp_store[email]
    return jsonify({"message": "OTP verified successfully!"}), 200

if __name__ == "__main__":
    app.run(debug=True)
