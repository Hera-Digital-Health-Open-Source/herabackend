from django.test import TestCase
from unittest.mock import patch

from webhook_survey_responses.utils import handle_response
from webhook_survey_responses.utils import get_matched_vaccine_ids
from webhook_survey_responses.utils import update_child_past_vaccination
from webhook_survey_responses.utils import update_survey_response
from hera.secrets import STATIC_TOKEN
from child_health.models import Vaccine
import requests


class TestHandleResponse(TestCase):
    def test_yes(self):
        self.assertEqual(handle_response("yes"), "yes")

    def test_no(self):
        self.assertEqual(handle_response("no"), "no")

    def test_evet(self):
        self.assertEqual(handle_response("evet"), "yes")

    def test_hayir(self):
        self.assertEqual(handle_response("hayır"), "no")

    def test_نعم(self):
        self.assertEqual(handle_response("نعم"), "yes")

    def test_لا(self):
        self.assertEqual(handle_response("لا"), "no")

    def test_empty(self):
        self.assertEqual(handle_response(""), "")


class TestGetMatchedVaccineIds(TestCase):
    MALE_VACCINE_FIRST_DOSE_WEEK = 1
    MALE_VACCINE_SECOND_DOSE_WEEK = 3
    FEMALE_VACCINE_FIRST_DOSE_WEEK = 2
    FEMALE_VACCINE_SECOND_DOSE_WEEK = 4
    UNIVERSAL_VACCINE_FIRST_DOSE_WEEK = 1
    UNIVERSAL_VACCINE_SECOND_DOSE_WEEK = 100

    def setUp(self) -> None:
        self.base_url = "https://exciting-simply-hippo.ngrok-free.app"
        Vaccine.objects.create(
            name='universal_vaccine1',
            nickname='UniVax1',
            applicable_for_male=True,
            applicable_for_female=True,
            is_active=True,
        )

        Vaccine.objects.create(
            name='universal_vaccine2',
            nickname='UniVax2',
            applicable_for_male=True,
            applicable_for_female=True,
            is_active=True,
        )

        self.patch_requests()

    def patch_requests(self):
        return_obj = requests.Response()
        return_obj.status_code = 200
        return_obj.json = lambda: [{"id": 1, "name": "universal_vaccine1"}, {"id": 2, "name": "universal_vaccine2"}]

        patcher = patch.object(requests, 'get', return_value=return_obj)
        self.addCleanup(patcher.stop)
        _ = patcher.start()

    def test_empty(self):
        self.assertEqual(get_matched_vaccine_ids(self.base_url, STATIC_TOKEN, []), [])

    def test_no_match(self):
        self.assertEqual(get_matched_vaccine_ids(self.base_url, STATIC_TOKEN, ["a", "b"]), [])

    def test_match(self):
        matched_ids = get_matched_vaccine_ids(self.base_url, STATIC_TOKEN, ["universal_vaccine1", "universal_vaccine2"])
        
        self.assertEqual(matched_ids, [1, 2])
