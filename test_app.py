import unittest
from unittest.mock import patch, MagicMock
from Principal import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        # Configura el cliente de prueba
        self.app = app.test_client()
        self.app.testing = True

    @patch('Principal.get_connection')
    def test_index_con_formulario(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'Colegio A'), (2, 'Colegio B')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Colegio A', response.data)
        self.assertIn(b'<form', response.data)  # Verifica que el form existe
        self.assertIn(b'name="fecha"', response.data)
        self.assertIn(b'name="colegio"', response.data)
        self.assertIn(b'name="operario"', response.data)

    @patch('Principal.get_connection')
    def test_obtener_prendas(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'Prenda A'), (2, 'Prenda B')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.app.get('/prendas/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Prenda A', response.data)

    @patch('Principal.get_connection')
    def test_obtener_operaciones(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'Operacion A', 1000), (2, 'Operacion B', 2000)]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.app.get('/operaciones/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Operacion A', response.data)

    @patch('Principal.get_connection')
    def test_guardar_exitoso(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1000]  # Costo de la operación
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        data = {
            'fecha': '2024-04-25',
            'hora': '10:00',
            'colegio': '1',
            'prenda': '1',
            'operacion': '1',
            'cantidad': '5',
            'operario': 'Juan Perez',
            'horas_diurnas': '2',
            'horas_nocturnas': '1',
            'horas_festivas_dia': '0',
            'horas_festivas_noche': '0',
            'horas_dominicales': '0',
            'tipo_incapacidad': 'ninguna',
            'dias_incapacidad': '0',
            'fecha_ingreso': '',
            'fecha_corte': ''
        }

        response = self.app.post('/guardar', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Juan Perez', response.data)

    @patch('Principal.get_connection')
    def test_guardar_error_db(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("Database error")
        mock_get_connection.return_value = mock_conn

        data = {
            'fecha': '2024-04-25',
            'hora': '10:00',
            'colegio': '1',
            'prenda': '1',
            'operacion': '1',
            'cantidad': '5',
            'operario': 'Juan Perez',
            'horas_diurnas': '0',
            'horas_nocturnas': '0',
            'horas_festivas_dia': '0',
            'horas_festivas_noche': '0',
            'horas_dominicales': '0',
            'tipo_incapacidad': 'ninguna',
            'dias_incapacidad': '0',
            'fecha_ingreso': '',
            'fecha_corte': ''
        }

        response = self.app.post('/guardar', data=data)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Error', response.data)

    def test_guardar_datos_incompletos(self):
        response = self.app.post('/guardar', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Campos requeridos', response.data)

    @patch('Principal.get_connection')
    def test_prendas_id_invalido(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.app.get('/prendas/999')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'[]', response.data)

    @patch('Principal.get_connection')
    def test_operaciones_id_invalido(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.app.get('/operaciones/999')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'[]', response.data)

if __name__ == '__main__':
    unittest.main()