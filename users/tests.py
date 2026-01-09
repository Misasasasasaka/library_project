import json
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthCaptchaEmailCodeTests(TestCase):
    def test_captcha_endpoint_sets_session(self):
        resp = self.client.get("/api/auth/captcha")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("image/svg+xml", resp.headers.get("Content-Type", ""))
        self.assertIsNotNone(self.client.session.get("auth_captcha"))

    def test_login_requires_captcha(self):
        User = get_user_model()
        User.objects.create_user(username="user1", password="pass12345")

        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"username": "user1", "password": "pass12345"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json().get("ok"))

    def test_register_flow_requires_email_code_and_captcha(self):
        captcha_resp = self.client.get("/api/auth/captcha")
        self.assertEqual(captcha_resp.status_code, 200)
        captcha_text = (self.client.session.get("auth_captcha") or {}).get("text")
        self.assertTrue(captcha_text)

        email_addr = "newuser@example.com"
        send_resp = self.client.post(
            "/api/auth/email-code",
            data=json.dumps({"mail": email_addr, "captcha": captcha_text}),
            content_type="application/json",
        )
        self.assertEqual(send_resp.status_code, 200)
        self.assertTrue(send_resp.json().get("ok"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(email_addr, mail.outbox[0].to)

        match = re.search(r"\b(\d{6})\b", mail.outbox[0].body or "")
        self.assertIsNotNone(match)
        code = match.group(1)

        resp = self.client.post(
            "/api/auth/register",
            data=json.dumps(
                {
                    "username": "newuser",
                    "password": "pass12345",
                    "mail": email_addr,
                    "email_code": code,
                    "captcha": captcha_text,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json().get("ok"))

        User = get_user_model()
        self.assertTrue(User.objects.filter(username="newuser", mail=email_addr).exists())

        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.json().get("ok"))
