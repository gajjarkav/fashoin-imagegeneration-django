import io
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

class TestFluxAPI(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/api/v1/images/edit'
        
        # Valid image mock
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xfa\xcf\x00\x00\x02\x07\x01\x02\x9a\x1c1q\x00\x00\x00\x00IEND\xaeB`\x82'
        self.valid_image = SimpleUploadedFile(
            name='test_image.png',
            content=image_content,
            content_type='image/png'
        )

    def test_missing_image(self):
        response = self.client.post(self.url, {'prompt': 'Change color'})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'Missing image file'})

    def test_missing_prompt(self):
        response = self.client.post(self.url, {'image': self.valid_image})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'Missing prompt'})

    def test_invalid_image_format(self):
        invalid_image = SimpleUploadedFile(
            name='test.txt',
            content=b'this is not an image',
            content_type='text/plain'
        )
        response = self.client.post(self.url, {
            'image': invalid_image,
            'prompt': 'Change color'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported image format', response.json()['error'])

    @patch('stylist.services.flux.requests.post')
    @patch('stylist.services.flux.settings')
    def test_successful_flux_request(self, mock_settings, mock_post):
        mock_settings.AZURE_FLUX_ENDPOINT = 'https://mock.api.cognitive.microsoft.com'
        mock_settings.AZURE_FLUX_API_KEY = 'mock_key'
        mock_settings.AZURE_FLUX_MODEL = 'flux.2-pro'
        mock_settings.AZURE_FLUX_API_VERSION = 'preview'
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'result': {'image': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD'}
        }
        
        self.valid_image.seek(0)
        response = self.client.post(self.url, {
            'image': self.valid_image,
            'prompt': 'Change color'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('image_url', data)
        self.assertEqual(data['model'], 'FLUX.2-pro')
        
    @patch('stylist.services.flux.requests.post')
    @patch('stylist.services.flux.settings')
    def test_azure_401(self, mock_settings, mock_post):
        mock_settings.AZURE_FLUX_ENDPOINT = 'https://mock'
        mock_settings.AZURE_FLUX_API_KEY = 'mock_key'
        
        mock_post.return_value.status_code = 401
        
        self.valid_image.seek(0)
        response = self.client.post(self.url, {
            'image': self.valid_image,
            'prompt': 'Change color'
        })
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('improperly configured', response.json()['error'])

    @patch('stylist.services.flux.requests.post')
    @patch('stylist.services.flux.settings')
    def test_azure_429(self, mock_settings, mock_post):
        mock_settings.AZURE_FLUX_ENDPOINT = 'https://mock'
        mock_settings.AZURE_FLUX_API_KEY = 'mock_key'
        
        mock_post.return_value.status_code = 429
        
        self.valid_image.seek(0)
        response = self.client.post(self.url, {
            'image': self.valid_image,
            'prompt': 'Change color'
        })
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('Rate limit', response.json()['error'])

    @patch('stylist.services.flux.requests.post')
    @patch('stylist.services.flux.settings')
    def test_azure_5xx(self, mock_settings, mock_post):
        mock_settings.AZURE_FLUX_ENDPOINT = 'https://mock'
        mock_settings.AZURE_FLUX_API_KEY = 'mock_key'
        
        mock_post.return_value.status_code = 503
        
        self.valid_image.seek(0)
        response = self.client.post(self.url, {
            'image': self.valid_image,
            'prompt': 'Change color'
        })
        
        self.assertEqual(response.status_code, 502)
        
    @patch('stylist.services.flux.requests.post')
    @patch('stylist.services.flux.settings')
    def test_malformed_response(self, mock_settings, mock_post):
        mock_settings.AZURE_FLUX_ENDPOINT = 'https://mock'
        mock_settings.AZURE_FLUX_API_KEY = 'mock_key'
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'weird_key': 'no_image_here'
        }
        
        self.valid_image.seek(0)
        response = self.client.post(self.url, {
            'image': self.valid_image,
            'prompt': 'Change color'
        })
        
        self.assertEqual(response.status_code, 502)
