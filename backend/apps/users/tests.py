import factory
import json
import random
from importlib import import_module

from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from users.test.factory import *
from users.models import *
from users.views import *
from faker import Faker
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory, force_authenticate

from users import views, util

from rest_framework.renderers import JSONRenderer

from backend.settings.common import AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_URL

import boto3


def convert_to_dict_from(model):
    data = { key: value if type(value) is str or type(value) is int else str(value)
        for key, value in model.__dict__.items() if key is not '_state' and value is not None }
    return data


def create_test_data():
    util.prepare()
    User.objects.create_superuser("tomoya", "tomoya@example.com", "youluck123")
    User.objects.create_guest_user("guest")
    User.objects.create_unique_user("general@example.com", username="general")
    User.objects.create_researcher("researcher", "researcher@example.com", "password")
    

class EmailUserAPITestCase(APITestCase):
    def setUp(self):
        create_test_data()
    
    def test_get_emailuser(self):
        user = EmailUserFactory.create(password="password")
        self.assertTrue(self.client.login(username="tomoya", password="youluck123"))
        response = self.client.get(f"/api/users/{user.id}/")
        self.assertTrue(response.status_code == 200)


class DownloadEmailListAPITestCase(APITestCase):
    def setUp(self):
        create_test_data()

    def test_is_accessible_to_get_download_curve_data(self):
        request = RequestFactory.create(participants=[EmailUserFactory.create() for _ in range(10)])
        for _ in range(5):
            CurveFactory.create(room_name=request.room_name)
        response = self.client.get(f"/api/get_download_curve_data/{request.id}")
        self.assertTrue(response.status_code == 200)
        self.assertTrue("url" in response.json())
    
    def test_is_inaccessible_to_get_download_curve_data(self):
        response = self.client.get(f"/api/get_download_curve_data/{100}")
        self.assertTrue(response.status_code == 404)


class DownloadCurveAPITestCase(APITestCase):
    def setUp(self):
        create_test_data()

    def test_is_accessible_to_get_download_curve_data(self):
        curve_ids = []
        for _ in range(8):
            curve_ids.append(str(CurveFactory.create().id))
        url = f"/api/download_curve_data/?ids={','.join(curve_ids)}"
        user = EmailUserFactory.create()
        user.set_password("12345")
        user.save()
        self.client.login(username=user.username, password="12345")
        response = self.client.get(url)
        self.assertTrue(response.status_code == 200)
        self.assertTrue("url" in response.json())


    def test_is_accessible_to_get_download_many_curve_data(self):
        curve_ids = []
        for _ in range(11):
            curve_ids.append(str(CurveFactory.create().id))
        url = f"/api/download_curve_data/?ids={','.join(curve_ids)}"
        user = EmailUserFactory.create()
        user.set_password("12345")
        user.save()
        self.client.login(username=user.username, password="12345")
        response = self.client.get(url)
        self.assertTrue(response.status_code == 403)


class LoginAPITestCase(APITestCase):
    def setUp(self):
        create_test_data()
    
    def test_is_get_login_api(self):
        module = import_module(os.environ.get('DJANGO_SETTINGS_MODULE'))
        queries = "?key=test"
        response = self.client.get(f"/api/login/{queries}")
        self.assertTrue(response.status_code == 302)
        self.assertTrue(response.url == f"{module.APPLICATION_URL}app/login/{queries}")
    
    def test_is_post_login_api_with_guest2(self):
        module = import_module(os.environ.get('DJANGO_SETTINGS_MODULE'))
        queries = "?guest=true"
        response = self.client.post(f"/api/login/{queries}")
        self.assertEqual(302, response.status_code)
    
    def test_is_post_login_api_with_guest3(self):
        requests = [RequestFactory.create() for _ in range(5)]
        module = import_module(os.environ.get('DJANGO_SETTINGS_MODULE'))
        queries = f"?guest=true&passport={','.join(list(map(lambda item: str(item.id), requests)))}"
        response = self.client.post(f"/api/login/{queries}")
        self.assertEqual(302, response.status_code)
    
    def test_is_correct_result_to_return_invalid_email(self):
        self.assertTrue(LoginAPIView.is_invalid_emailuser("emonotate+abcdef@gmail.com"))
        self.assertFalse(LoginAPIView.is_invalid_emailuser("abcdef@gmail.com"))
    
    def test_is_user_with_invalid_email(self):
        module = import_module(os.environ.get('DJANGO_SETTINGS_MODULE'))
        queries = "?guest=true"
        response = self.client.post(f"/api/login/{queries}")
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{module.APPLICATION_URL}app/change_email/", response.url)


class SendMailAPITestCase(APITestCase):
    def setUp(self):
        create_test_data()
    
    def test_is_access_send_all_mails_in_request(self):
        participants = [EmailUserFactory.create() for _ in range(10)]
        request = RequestFactory.create(participants=participants)
        response = self.client.get(f"/api/send/{request.id}")
        self.assertTrue(response.status_code == 200)

        def handle(participant, req):
            return participant.relationparticipant_set.get(request=req)

        memberships = [handle(participant, request) for participant in participants]
        self.assertTrue(all([membership.sended_mail for membership in memberships]))

    def test_is_access_send_some_mails_in_request(self):
        participants = [EmailUserFactory.create() for _ in range(10)]
        NUM_SAMPLE = 5
        targets = random.sample(participants, NUM_SAMPLE)
        request = RequestFactory.create(participants=participants)
        url = f"/api/send/{request.id}?targets={';'.join([str(target.id) for target in targets])}"
        response = self.client.get(url)
        self.assertTrue(response.status_code == 200)

        def handle(participant, req):
            return participant.relationparticipant_set.get(request=req)

        memberships = [handle(participant, request) for participant in participants]
        self.assertTrue(sum([membership.sended_mail for membership in memberships]) == NUM_SAMPLE)
    
    def test_is_access_send_some_duplicate_mails_in_request(self):
        participants = [EmailUserFactory.create() for _ in range(10)]
        NUM_SAMPLE = 5
        NUM_SAMPLE2 = 2
        targets = random.sample(participants, NUM_SAMPLE)
        targets2 = random.sample(targets, NUM_SAMPLE2)
        targets.extend(targets2)
        request = RequestFactory.create(participants=participants)
        url = f"/api/send/{request.id}?targets={';'.join([str(target.id) for target in targets])}"
        response = self.client.get(url)
        self.assertTrue(response.status_code == 200)
        def handle(participant, req):
            return participant.relationparticipant_set.get(request=req)
        memberships = [handle(participant, request) for participant in participants]
        self.assertTrue(sum([membership.sended_mail for membership in memberships]) == NUM_SAMPLE)


class ResetEmailAddressesFromRequest(APITestCase):
    def setUp(self):
        create_test_data()
    
    def test_is_accessible_to_reset_email_addresses_api(self):
        request = RequestFactory.create(participants=[EmailUserFactory.create() for _ in range(10)])
        response = self.client.get(f"/api/reset_email_addresses/{request.id}")
        self.assertTrue(response.status_code == 200)


class EmailUserTest(TestCase):
    def setUp(self):
        pass
    
    def test_is_including_email_when_create_superuser(self):
        self.assertTrue("email" in EmailUser.REQUIRED_FIELDS)
