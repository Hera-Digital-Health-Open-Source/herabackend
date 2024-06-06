from django.test import TestCase

from .utils import mask_username


class CustomUserTests(TestCase):
    def setUp(self):
        pass

    def test_mask_username(self):
        result = mask_username("+1202999999")
        self.assertEqual(result, "+1202******")
