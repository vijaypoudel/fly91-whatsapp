from flask import Flask, request, jsonify
import os
import boto3
import json
from twilio.rest import Client
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
from flasgger import Swagger
from urllib.parse import quote

load_dotenv()

app = Flask(__name__)
swagger = Swagger(app)
# Function to retrieve secrets from AWS Secrets Manager
def get_secret():
    secret_name = "prod/fly91/whatsapp"
    region_name = "eu-north-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    secret_client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = secret_client.get_secret_value(SecretId=secret_name)
        print(get_secret_value_response)
        secret = get_secret_value_response["SecretString"]
        return json.loads(secret)
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise RuntimeError(f"Failed to retrieve secrets: {e}")

secrets = get_secret()
if secrets:
    TWILIO_ACCOUNT_SID = secrets.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = secrets.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER ='whatsapp:+14155238886' # Replace with your Twilio WhatsApp number

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    @app.route('/send_message', methods=['POST'])
    def send_message():
        """
              Send a WhatsApp message
              ---
              tags:
                - WhatsApp
              parameters:
                - name: body
                  in: body
                  required: true
                  schema:
                    type: object
                    required:
                      - to
                      - message
                    properties:
                      to:
                        type: string
                        description: The recipient's phone number
                      message:
                        type: string
                        description: The message to send
              responses:
                200:
                  description: Message sent successfully
                  schema:
                    type: object
                    properties:
                      status:
                        type: string
                      message_sid:
                        type: string
                400:
                  description: Error sending message
                  schema:
                    type: object
                    properties:
                      status:
                        type: string
                      message:
                        type: string
              """
        try:
            data = request.get_json()
            to_number = data['to']
            message_body = data['message']

            message = client.messages.create(
                body=message_body,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=f'whatsapp:{to_number}'
            )
            print(message)
            return jsonify({'status': 'success', 'message_sid': message.sid}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

    if __name__ == '__main__':
        app.run(debug=True)
else:
    raise RuntimeError("Failed to retrieve secrets from AWS Secrets Manager")
