from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import requests
import os
import json

# In-memory storage for message statuses
# Format: {message_id: {'status': 'sent/delivered/read', 'timestamp': '...'}}
message_statuses = {}

# In-memory storage for incoming messages
# Format: {message_id: {'from': '...', 'text': '...', 'timestamp': '...', 'type': '...'}}
incoming_messages = {}

# Verify token for webhook verification (you can change this to any secret string)
VERIFY_TOKEN = "my_secret_verify_token_12345"


def index(request):
    return render(request, 'index.html')


@csrf_exempt
def send_whatsapp(request):
    if request.method == 'POST':
        url = f"https://graph.facebook.com/v22.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"

        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": os.getenv('WHATSAPP_RECIPIENT_NUMBER'),
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {"code": "en_US"}
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

            if response.status_code == 200:
                # Extract message_id from the response
                message_id = data.get('messages', [{}])[0].get('id', 'unknown')

                # Store initial status as 'sent'
                message_statuses[message_id] = {
                    'status': 'sent',
                    'timestamp': data.get('messages', [{}])[0].get('message_status', 'sent')
                }

                print(f"Message sent! ID: {message_id}")
                return JsonResponse({
                    'success': True,
                    'message': 'Message sent successfully!',
                    'message_id': message_id
                })
            else:
                return JsonResponse({'success': False, 'error': str(data)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'POST method required'})


@csrf_exempt
def webhook(request):
    """
    Webhook endpoint for WhatsApp
    - Handles GET requests for verification
    - Handles POST requests for incoming events
    """

    if request.method == 'GET':
        # Webhook verification
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        print(f"Webhook verification attempt - Mode: {mode}, Token: {token}")

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("Webhook verified successfully!")
            return JsonResponse(int(challenge), safe=False)
        else:
            print("Webhook verification failed!")
            return JsonResponse({'error': 'Verification failed'}, status=403)

    elif request.method == 'POST':
        # Webhook event received
        try:
            body = json.loads(request.body.decode('utf-8'))
            print("\n" + "=" * 50)
            print("WEBHOOK EVENT RECEIVED:")
            print(json.dumps(body, indent=2))
            print("=" * 50 + "\n")

            # Extract status updates from the webhook payload
            entries = body.get('entry', [])

            for entry in entries:
                changes = entry.get('changes', [])

                for change in changes:
                    value = change.get('value', {})

                    # Check for status updates
                    statuses = value.get('statuses', [])
                    for status in statuses:
                        message_id = status.get('id')
                        status_type = status.get('status')  # sent, delivered, read, failed
                        timestamp = status.get('timestamp')

                        if message_id:
                            # Update the status in our storage
                            message_statuses[message_id] = {
                                'status': status_type,
                                'timestamp': timestamp
                            }
                            print(f"Status updated - Message ID: {message_id}, Status: {status_type}")

                    # Check for incoming messages (if user replies)
                    messages = value.get('messages', [])
                    for message in messages:
                        from_number = message.get('from')
                        message_id = message.get('id')
                        message_type = message.get('type')
                        timestamp = message.get('timestamp')

                        if message_type == 'text':
                            text_body = message.get('text', {}).get('body', '')

                            # Store incoming message
                            incoming_messages[message_id] = {
                                'from': from_number,
                                'text': text_body,
                                'timestamp': timestamp,
                                'type': message_type
                            }

                            print(f"Incoming message from {from_number}: {text_body}")

            return JsonResponse({'status': 'received'}, status=200)

        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_status(request):
    """
    API endpoint to get the current status of a message
    """
    message_id = request.GET.get('message_id')

    if not message_id:
        return JsonResponse({'error': 'message_id required'}, status=400)

    status_data = message_statuses.get(message_id, {'status': 'unknown', 'timestamp': None})

    return JsonResponse({
        'message_id': message_id,
        'status': status_data['status'],
        'timestamp': status_data['timestamp']
    })


def get_all_statuses(request):
    """
    API endpoint to get all message statuses (for debugging)
    """
    return JsonResponse({
        'statuses': message_statuses,
        'count': len(message_statuses)
    })


def get_incoming_messages(request):
    """
    API endpoint to get all incoming messages
    """
    # Convert to list and sort by timestamp (most recent first)
    messages_list = []
    for msg_id, msg_data in incoming_messages.items():
        messages_list.append({
            'id': msg_id,
            'from': msg_data['from'],
            'text': msg_data['text'],
            'timestamp': msg_data['timestamp'],
            'type': msg_data['type']
        })

    # Sort by timestamp descending (most recent first)
    messages_list.sort(key=lambda x: int(x['timestamp']), reverse=True)

    return JsonResponse({
        'messages': messages_list,
        'count': len(messages_list)
    })