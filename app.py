from flask import Flask, request, redirect, render_template, jsonify
import smtplib
from email.message import EmailMessage
import os
import ai_bridge

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

EMAIL_ADDRESS = 'gjsamo1996@gmail.com'  # Your email
EMAIL_PASSWORD = 'hxkm cblk lqmu ceip'  # Gmail App Password
ai_bridge.init_bot()
@app.route('/')
def home():
    return render_template('index.html')

# 🔹 Route for each page
@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/order')
def order():
    return render_template('order.html')

@app.route('/thank-you.html')
def thank_you():
    return render_template('thank-you.html')
@app.route('/upload.html')
def upload():
    return render_template('upload.html')
# 🔹 Route to serve uploaded files (if needed)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_question = data.get('question', '')
    if not user_question.strip():
        return jsonify({'response': "Please enter a valid question."})

    response = ai_bridge.ask_bot(user_question)
    return jsonify({'response': response})
@app.route('/send', methods=['POST'])
def send():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        plan = request.form.get('plan')
        file = request.files.get('file')

        if not email or '@' not in email:
            return "Invalid email format"

        # First Email (to yourself)
        msg = EmailMessage()
        msg['Subject'] = 'New Contact Form Submission'
        msg['From'] = email
        msg['To'] = EMAIL_ADDRESS
        msg.set_content(f"Name: {name}\nEmail: {email}\nMessage: {message}\nPlan: {plan}", subtype='plain')
        msg.add_alternative(f"""
        <html>
            <body>
                <p>Name: {name}<br>
                   Email: {email}<br>
                   Message: {message}<br>
                   Plan: {plan}
                </p>
            </body>
        </html>
        """, subtype='html')

        if file and file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            with open(filepath, 'rb') as f:
                file_data = f.read()
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file.filename)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)

            # Second Email (confirmation to user)
            confirm = EmailMessage()
            confirm['Subject'] = 'Confirmation Email'
            confirm['From'] = EMAIL_ADDRESS
            confirm['To'] = email
            confirm.add_alternative(f"""
            <html>
                <body>
                    <p>Hi {name},<br><br>
                    Thanks for using <strong>BotFriendly</strong>! 🎉<br><br>
                    Your application has been received with the email: <strong>{email}</strong>.<br><br>
                    To move forward, please provide us with:<br>
                    <ul>
                      <li>Your company’s website</li>
                      <li>A <strong>.txt file</strong> (or just a message) with any details the bot will need. If you need a connection to something schedule or something we will contact you on how to do it</li>
                    </ul>
                    You can either:
                    <ul>
                      <li><strong>Reply directly to this email</strong> with that information,</li>
                      <li>Or upload your details securely at this link: 
                        <a href='https://yourdomain.com/bot-info-upload'>Submit Bot Info</a></li>
                    </ul>
                    Thanks again for choosing us – we’re excited to build something smart for you!<br><br>
                    — The BotFriendly Team 🤖
                    </p>
                </body>
            </html>
            """, subtype='html')

            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(confirm)

            return redirect('/thank-you.html')

        except Exception as e:
            return f"Email sending failed: {e}"

    return "Invalid request", 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)