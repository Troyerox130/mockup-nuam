from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import CalificacionTributaria


class CargasMasivasTests(TestCase):
    def setUp(self):
        self.registro_2025 = CalificacionTributaria.objects.create(
            periodo_comercial=2025,
            ejercicio='2025',
            instrumento='ABC',
            fecha_pago=date(2025, 1, 15),
            descripcion='Registro 2025',
        )
        self.otro_registro_2025 = CalificacionTributaria.objects.create(
            periodo_comercial=2025,
            ejercicio='2025',
            instrumento='DEF',
            fecha_pago=date(2025, 2, 15),
            descripcion='Otro registro 2025',
        )
        self.registro_2026 = CalificacionTributaria.objects.create(
            periodo_comercial=2026,
            ejercicio='2026',
            instrumento='GHI',
            fecha_pago=date(2026, 1, 15),
            descripcion='Registro 2026',
        )

    def test_carga_factor_actualiza_el_factor_elegido_en_el_periodo(self):
        response = self.client.post(
            reverse('carga_factor'),
            {
                'periodo_factor': '2025',
                'campo_factor': 'factor_08',
                'valor_factor': '1.23456789',
            },
        )

        self.assertRedirects(response, reverse('lista_calificaciones'))
        self.registro_2025.refresh_from_db()
        self.otro_registro_2025.refresh_from_db()
        self.registro_2026.refresh_from_db()
        self.assertEqual(self.registro_2025.factor_08, Decimal('1.23456789'))
        self.assertEqual(self.otro_registro_2025.factor_08, Decimal('1.23456789'))
        self.assertIsNone(self.registro_2026.factor_08)

    def test_carga_monto_actualiza_el_periodo_sin_afectar_otros_periodos(self):
        response = self.client.post(
            reverse('carga_monto'),
            {'periodo_monto': '2025', 'valor_monto': '50000.25'},
        )

        self.assertRedirects(response, reverse('lista_calificaciones'))
        self.registro_2025.refresh_from_db()
        self.otro_registro_2025.refresh_from_db()
        self.registro_2026.refresh_from_db()
        self.assertEqual(self.registro_2025.monto, Decimal('50000.25'))
        self.assertEqual(self.otro_registro_2025.monto, Decimal('50000.25'))
        self.assertIsNone(self.registro_2026.monto)

    def test_carga_factor_rechaza_un_nombre_de_campo_no_permitido(self):
        response = self.client.post(
            reverse('carga_factor'),
            {
                'periodo_factor': '2025',
                'campo_factor': 'descripcion',
                'valor_factor': '1.00000000',
            },
        )

        self.assertRedirects(response, reverse('lista_calificaciones'))
        self.registro_2025.refresh_from_db()
        self.assertIsNone(self.registro_2025.factor_actualizacion)

    def test_botones_ver_formato_abren_modal_y_cierran_modal_carga(self):
        response = self.client.get(reverse('lista_calificaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'data-bs-toggle="modal" data-bs-target="#modalFormato" data-bs-dismiss="modal"',
            count=2,
        )
