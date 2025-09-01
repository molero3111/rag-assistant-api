from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

class RagChatEndpointTests(APITestCase):
    def test_rag_chat_success(self):
        url = reverse('rag_chat')
        data = {'prompt': 'Explain the Pythagorean theorem with an example.'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn('response', response.data)
        self.assertTrue(response.data['response'])

    def test_rag_chat_missing_prompt(self):
        url = reverse('rag_chat')
        data = {}  # No prompt
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
