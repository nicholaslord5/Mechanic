import unittest
import json
from datetime import date
from werkzeug.security import generate_password_hash
from mech import create_app
from mech.extensions import db
from mech.models import Customer

class CustomerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            #### seed a customer for login/delete tests
            cust = Customer(
                name='Seed User',
                email='seed@example.com',
                phone='555-0000',
                password=generate_password_hash('seedpass')
            )
            db.session.add(cust)
            db.session.commit()
            self.seed_id = cust.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_customer_success(self):
        payload = {
            'name': 'Lizzy',
            'email': 'lizzy@example.com',
            'phone': '555-1234',
            'password': 'LizzyPass'
        }
        resp = self.client.post(
            '/customers/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertIn('id', body)
        self.assertEqual(body['email'], payload['email'])

    def test_create_customer_missing_field(self):
        payload = {'name': 'Bob'}  #### missing email/phone/password
        resp = self.client.post(
            '/customers/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_customer_login_success(self):
        payload = {'email': 'seed@example.com', 'password': 'seedpass'}
        resp = self.client.post(
            '/customers/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('auth_token', body)
        self.assertEqual(body['status'], 'success')

    def test_customer_login_invalid(self):
        payload = {'email': 'seed@example.com', 'password': 'wrong'}
        resp = self.client.post(
            '/customers/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

    def test_list_customers_pagination(self):
        #### create extra to test pagination
        with self.app.app_context():
            db.session.add(Customer(
                name='Extra',
                email='extra@example.com',
                phone='555-1111',
                password=generate_password_hash('x')
            ))
            db.session.commit()
        resp = self.client.get('/customers/?page=1&per_page=1')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIsInstance(body['customers'], list)
        self.assertIn('meta', body)

    def test_update_customer_success(self):
        payload = {'phone': '999-9999'}
        resp = self.client.put(
            f'/customers/{self.seed_id}',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['phone'], '999-9999')

    def test_update_customer_not_found(self):
        resp = self.client.put(
            '/customers/999',
            data=json.dumps({'name':'X'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_customer_requires_auth(self):
        ### without token
        resp = self.client.delete('/customers/')
        self.assertEqual(resp.status_code, 401)

    def test_delete_customer_success(self):
        ### login to get token
        login = self.client.post(
            '/customers/login',
            data=json.dumps({'email':'seed@example.com','password':'seedpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.delete(
            '/customers/',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('deleted customer', resp.get_json()['message'])

if __name__ == '__main__':
    unittest.main()
