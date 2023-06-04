import smtplib
import pickle
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from googletrans import Translator

load_dotenv()

DEBUG = True  # Set this to False when you're done debugging

def translate_to_chinese(sentence):
    translator = Translator()
    translation = translator.translate(sentence, dest='zh-tw')
    return f"{sentence}({translation.text})"

def printd(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def send_email(text, subject):
    your_email = os.getenv('YOUR_EMAIL')
    your_password = os.getenv('YOUR_PASSWORD')
    
    # Replace this with the recipient email (in this case, your email)
    recipient_email = os.getenv('RECEIVE_EMAIL')
    
    # Create the MIME object
    msg = MIMEMultipart()
    msg['From'] = your_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    # Email body
    body = text
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(your_email, your_password)
        text = msg.as_string()
        server.sendmail(your_email, recipient_email, text)
        server.quit()
        printd("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def save_list_to_file(data, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(data, file)

def load_list_from_file(file_name):
    if not os.path.exists(file_name):
        print(f"File '{file_name}' not found. Returning an empty list.")
        return []

    with open(file_name, 'rb') as file:
        data = pickle.load(file)
    return data

def get_article_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    content = soup.find('div', class_='caas-body')

    return content
