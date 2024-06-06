import json
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from .models import HealthCenter
from .serializer import HealthCentersSirializer
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import pytz

@csrf_exempt
def health_centers_list(request):
    if request.method == 'GET':
        is_disaster_param = request.GET.get('is_disaster', None)
        health_centers = HealthCenter.objects.all()
        if is_disaster_param == 'true':
            health_centers = health_centers.filter(is_disaster=True)
        serializer = HealthCentersSirializer(health_centers, many=True)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        data = json.loads(request.body)

        naive_datetime = datetime.strptime(data["last_updated"], "%Y-%m-%dT%H:%M:%S.%fZ")
        time_zone = pytz.timezone('Europe/Istanbul')
        last_updated = time_zone.localize(naive_datetime)

        update_data = {
            "name": data["name"],
            "address": data["address"],
            "geolocation": data["geolocation"],
            "activity_state": data["activity_state"],
            "type": data["type"],
            "last_updated": last_updated,
        }

        try:
            health_center, created = HealthCenter.objects.update_or_create(
                name=data["name"],
                defaults=update_data
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Wrong Request'})
