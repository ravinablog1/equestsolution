from django.shortcuts import render
import time
from datetime import datetime, timedelta
import requests
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.decorators import api_view

THRESHOLD_1 = 10  # Number of attempts allowed within 20 seconds
THRESHOLD_2 = 100  # Number of attempts allowed within 1 minute
BLOCK_TIME = 20 * 60  # 20 minutes in seconds


@api_view(['GET'])
def validate_ddos(request):
    ip = request.META.get('REMOTE_ADDR')
    bearer_key = request.META.get('HTTP_AUTHORIZATION')

    if bearer_key != 'Bearer mf8nrqICaHYD1y8wRMBksWm7U7gLgXy1mSWjhI0q':
        return JsonResponse({'error': 'Invalid Bearer key'}, status=400)

    # Check if IP is blocked permanently
    if cache.get(f'blocked:{ip}'):
        return JsonResponse({'error': 'IP blocked permanently'}, status=400)

    now = datetime.now()
    recent_attempts = cache.get(f'attempts:{ip}')
    if recent_attempts:
        num_attempts, last_attempt_time = recent_attempts
        elapsed_time = (now - last_attempt_time).total_seconds()

        # Check if IP is blocked for 20 minutes
        if cache.get(f'blocked:{ip}') or elapsed_time < BLOCK_TIME:
            return JsonResponse({'error': 'IP blocked temporarily'}, status=400)

        # Reset attempts if more than 20 seconds have passed
        if elapsed_time > 20:
            cache.set(f'attempts:{ip}', (1, now), 20)
        else:
            # Check if threshold 1 is exceeded (10 attempts within 20 seconds)
            if num_attempts >= THRESHOLD_1:
                cache.set(f'blocked:{ip}', True, BLOCK_TIME)
                return JsonResponse({'error': 'IP blocked temporarily'}, status=400)
            cache.set(f'attempts:{ip}', (num_attempts + 1, last_attempt_time))
    else:
        cache.set(f'attempts:{ip}', (1, now), 20)

    # Check if threshold 2 is exceeded (100 attempts within 1 minute)
    if cache.incr(f'count:{ip}', 1) > THRESHOLD_2:
        cache.set(f'blocked:{ip}', True)
        return JsonResponse({'error': 'IP blocked permanently'}, status=400)

    # Return JSON response with random data from mockaroo.com
    # Replace 'YOUR_MOCKAROO_API_KEY' with your actual API key from mockaroo.com
    mockaroo_api_key = 'YOUR_MOCKAROO_API_KEY'
    # Generate and retrieve random data from Mockaroo API
    response = requests.get(f'https://api.mockaroo.com/api/generate.json?key={mockaroo_api_key}&count=1')

    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data[0])
    else:
        return JsonResponse({'error': 'Failed to retrieve data'}, status=500)
