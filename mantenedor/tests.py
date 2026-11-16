from django.test import TestCase, Client
from django.urls import reverse


class CsrfProtectionTests(TestCase):

    def setUp(self):
        # Crear un cliente que SÍ compruebe CSRF
        self.client = Client(enforce_csrf_checks=True)

        self.url = reverse('lista_calificaciones')

    def test_post_sin_token_csrf_es_rechazado(self):

        response = self.client.post(
            self.url,
            {
                'accion': 'grabar',
            }
        )

        self.assertEqual(response.status_code, 403)