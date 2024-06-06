import requests


def handle_response(raw_answer):
  raw_answer = raw_answer.lower()
  if raw_answer == "yes" or raw_answer == "evet" or raw_answer == "نعم":
    return "yes"
  elif raw_answer == "no" or raw_answer == "hayır" or raw_answer == "لا":
    return "no"

  return ""


def get_matched_vaccine_ids(base_url, token, vaccine_names):
  headers = {
    "Content-Type": "application/json",
    "Authorization": token
  }

  url = base_url + "/vaccines/"

  response = requests.get(url, headers=headers)

  if response.status_code >= 200 and response.status_code <= 299:
    all_vaccines = response.json()
    matched_vaccines_ids = [vaccine["id"] for vaccine in all_vaccines if vaccine["name"] in vaccine_names]

    return matched_vaccines_ids
  else:
    return []
  

def update_child_past_vaccination(base_url, token, vaccine_ids, child_id):
  headers = {
    "Content-Type": "application/json",
    "Authorization": token
  }
  
  data = {
    "past_vaccinations": vaccine_ids
  }

  url = base_url + "/children/" + child_id + "/"

  response = requests.patch(url, headers=headers, json=data)  

  return response.status_code >= 200 and response.status_code <= 299


def update_survey_response(base_url, token, survey_id, answer):
  headers = {
    "Content-Type": "application/json",
    "Authorization": token
  }
  
  data = {
    "response": answer
  }

  url = base_url + "/surveys/" + survey_id + "/response/"

  response = requests.post(url, headers=headers, json=data)  

  return response.status_code >= 200 and response.status_code <= 299
