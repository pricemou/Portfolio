"""
Tests unitaires de base pour l'application Flask
"""
import unittest
import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from utils.validators import validate_email, validate_url, sanitize_input, validate_required

class TestValidators(unittest.TestCase):
    """Tests pour les fonctions de validation"""
    
    def test_validate_email_valid(self):
        """Test la validation d'emails valides"""
        self.assertTrue(validate_email('test@example.com'))
        self.assertTrue(validate_email('user.name@domain.co.uk'))
        self.assertTrue(validate_email('test+tag@example.com'))
    
    def test_validate_email_invalid(self):
        """Test la validation d'emails invalides"""
        self.assertFalse(validate_email('invalid'))
        self.assertFalse(validate_email('@example.com'))
        self.assertFalse(validate_email('test@'))
        self.assertFalse(validate_email(''))
        self.assertFalse(validate_email(None))
    
    def test_validate_url_valid(self):
        """Test la validation d'URLs valides"""
        self.assertTrue(validate_url('https://example.com'))
        self.assertTrue(validate_url('http://www.example.com/path'))
        self.assertTrue(validate_url('https://example.com?param=value'))
    
    def test_validate_url_invalid(self):
        """Test la validation d'URLs invalides"""
        self.assertFalse(validate_url('not-a-url'))
        self.assertFalse(validate_url('ftp://example.com'))
    
    def test_sanitize_input(self):
        """Test le nettoyage des entrées"""
        self.assertEqual(sanitize_input('  test  '), 'test')
        self.assertEqual(sanitize_input('test', max_length=3), 'tes')
        self.assertEqual(sanitize_input(''), '')
        self.assertEqual(sanitize_input(None), '')
    
    def test_validate_required(self):
        """Test la validation des champs requis"""
        data = {'name': 'Test', 'email': 'test@example.com'}
        errors = validate_required(data, ['name', 'email'])
        self.assertEqual(len(errors), 0)
        
        data = {'name': ''}
        errors = validate_required(data, ['name', 'email'])
        self.assertEqual(len(errors), 2)

class TestAppRoutes(unittest.TestCase):
    """Tests pour les routes de l'application"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_route(self):
        """Test la route d'accueil"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_404_error(self):
        """Test la gestion des erreurs 404"""
        response = self.app.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_admin_login_get(self):
        """Test l'accès à la page de login admin"""
        response = self.app.get('/admin/login')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_route_redirect(self):
        """Test que /admin redirige vers /admin/login si non connecté"""
        response = self.app.get('/admin', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.location)

if __name__ == '__main__':
    unittest.main()


