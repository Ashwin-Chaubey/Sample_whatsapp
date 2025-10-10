from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import requests
import os


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
                return JsonResponse({'success': True, 'message': 'Message sent successfully!'})
            else:
                return JsonResponse({'success': False, 'error': str(data)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'POST method required'})