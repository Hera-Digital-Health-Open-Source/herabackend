from django.core.management.base import BaseCommand
import requests
from datetime import datetime
import pytz
from ...models import HealthCenter

class Command(BaseCommand):
    help = 'Seed locations from UNHCR'

    def handle(self, *args, **options):
        HealthCenter.objects.filter(sa_id__isnull=True).update(is_disaster=True)
        url = 'https://turkiye.servicesadvisor.net/api/services/coordinates'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                
                settings_url = 'https://turkiye.servicesadvisor.net/api/services/initialdata/tr'
                settings_response = requests.get(settings_url)
                if settings_response.status_code == 200:
                  settings_data = settings_response.json()
                  if 'data' in settings_data:

                    i=0
                    for item in data['data']:
                        if(item['c'] == 1665):
                            location_url = f'https://turkiye.servicesadvisor.net/api/services/item/{item["id"]}?lang=tr'
                            location_response = requests.get(location_url)
                            if location_response.status_code == 200:
                              location_data = location_response.json()
                              if 'data' in location_data:
                                name = location_data['data']['additional']
                                
                                terms = [int(x) for x in item['t'].split(",")]
                                type = ''
                                if 2213 in terms:
                                  type = 'DH'
                                elif 1951 in terms:
                                  type = 'DH'
                                elif 48295 in terms:
                                  type = 'GSM'
                                elif 3061 in terms:
                                  type = 'HSM'

                                if(name == ''):
                                  city = self.get_name_by_id(settings_data, item['cid'])
                                  district = self.get_name_by_id(settings_data, item['did'])
                                  category = ''
                                  if 2213 in terms:
                                    category = 'Devlet Hastanesi'
                                  elif 1951 in terms:
                                    category = 'Devlet Hastanesi' 
                                  elif 48295 in terms:
                                    category = 'Göçmen Sağlığı Merkezi'
                                  elif 3061 in terms:
                                    category = 'Halk Sağlığı Merkezi'
                                  if(category != ''):
                                    name = f'{category} - {city}/{district}'
                                
                                if(name != ''):
                                  current_time = datetime.now()
                                  time_zone = pytz.timezone('Europe/Istanbul')
                                  last_updated = current_time.astimezone(time_zone)
                                  
                                  update_data = {
                                    "name": name,
                                    "address": location_data['data']['address'],
                                    "geolocation": f'{item["lat"]},{item["lng"]}',
                                    "activity_state": 'Aktif',
                                    "type": type,
                                    "last_updated": last_updated,
                                    "is_disaster": False,
                                    "sa_id": int(item['id']),
                                  }

                                  try:
                                    health_center, created = HealthCenter.objects.get_or_create(
                                        name=name,
                                        defaults=update_data
                                    )
                                    if created:
                                      i += 1
                                  except Exception as e:
                                    print(e)

                    self.stdout.write(self.style.SUCCESS(f'Health Centers seed finished. {i}'))

    def get_name_by_id(self, data, desired_id):
      for term in data["data"]["terms"]:
          if term["id"] == desired_id:
              return term["name"]
      return None