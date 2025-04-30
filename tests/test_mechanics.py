import unittest
import json
from datetime import date
from werkzeug.security import generate_password_hash
from mech import create_app
from mech.extensions import db
from mech.models import Mechanic, Customer, ServiceTicket

class MechanicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            #### seed customer for ticket FK
            cust = Customer(
                name='Cust',
                email='cust@test.com',
                phone='555-0001',
                password=generate_password_hash('cpass')
            )
            db.session.add(cust)
            db.session.commit()
            self.customer_id = cust.id

            #### seed mechanic
            mech = Mechanic(
                name='John',
                email='john@ex.com',
                phone='555-0002',
                salary=50000,
                password=generate_password_hash('jpass')
            )
            db.session.add(mech)
            db.session.commit()
            self.mech_id = mech.id

            #### seed a ticket for assignment tests
            ticket = ServiceTicket(
                vin='VIN321',
                service_date=date(2025, 4, 22),
                service_desc='Test service',
                customer_id=self.customer_id
            )
            db.session.add(ticket)
            db.session.commit()
            self.ticket_id = ticket.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_mechanic_login_success(self):
        resp = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('auth_token', body)
        self.token = body['auth_token']

    def test_mechanic_login_failure(self):
        resp = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'wrong'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

    def test_create_mechanic(self):
        payload = {
            'name':'Max',
            'email':'Max@ex.com',
            'phone':'555-0003',
            'salary':60000,
            'password':'mpass'
        }
        resp = self.client.post(
            '/mechanics/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn('id', resp.get_json())

    def test_get_mechanics(self):
        resp = self.client.get('/mechanics/')
        self.assertEqual(resp.status_code, 200)
        arr = resp.get_json()
        self.assertIsInstance(arr, list)

    def test_ranked_mechanics_requires_auth(self):
        resp = self.client.get('/mechanics/ranked')
        self.assertEqual(resp.status_code, 401)

    def test_ranked_mechanics_success(self):
        #### login first
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.get(
            '/mechanics/ranked',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp.status_code, 200)
        arr = resp.get_json()
        self.assertIsInstance(arr, list)
        self.assertIn('ticket_count', arr[0])

    def test_assign_mechanic_to_ticket_success(self):
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.post(
            f'/mechanics/{self.mech_id}/tickets/{self.ticket_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('added to ticket', resp.get_json()['message'])

    def test_assign_mechanic_to_ticket_invalid(self):
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        #### invalid mech_id
        resp1 = self.client.post(
            f'/mechanics/999/tickets/{self.ticket_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp1.status_code, 404)
        #### invalid ticket_id
        resp2 = self.client.post(
            f'/mechanics/{self.mech_id}/tickets/999',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp2.status_code, 404)

    def test_update_mechanic_success(self):
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.put(
            f'/mechanics/{self.mech_id}',
            data=json.dumps({'phone':'555-9999'}),
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['phone'], '555-9999')

    def test_update_mechanic_not_found(self):
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.put(
            '/mechanics/999',
            data=json.dumps({'phone':'x'}),
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_mechanic_success(self):
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.delete(
            f'/mechanics/{self.mech_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_mechanic_not_found(self):
        login = self.client.post(
            '/mechanics/login',
            data=json.dumps({'email':'john@ex.com','password':'jpass'}),
            content_type='application/json'
        )
        token = login.get_json()['auth_token']
        resp = self.client.delete(
            '/mechanics/999',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
