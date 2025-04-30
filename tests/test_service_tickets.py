import unittest
import json
from datetime import date
from werkzeug.security import generate_password_hash
from mech import create_app
from mech.extensions import db
from mech.models import Customer, Mechanic, ServiceTicket

class ServiceTicketTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # seed a customer
            cust = Customer(
                name='Cust',
                email='cust@ex.com',
                phone='555-1000',
                password=generate_password_hash('cpass')
            )
            db.session.add(cust)
            # seed a mechanic
            mech = Mechanic(
                name='Mech',
                email='mech@ex.com',
                phone='555-2000',
                salary=40000,
                password=generate_password_hash('mpass')
            )
            db.session.add(mech)
            db.session.commit()
            self.mech_id = mech.id
            self.customer_id = cust.id
            self.token = self.client.post(
                '/mechanics/login',
                data=json.dumps({'email':'mech@ex.com','password':'mpass'}),
                content_type='application/json'
            ).get_json()['auth_token']

            # seed a ticket for update/delete
            ticket = ServiceTicket(
                vin='VIN001',
                service_date=date(2025, 4, 22),
                service_desc='Initial',
                customer_id=self.customer_id
            )
            db.session.add(ticket)
            db.session.commit()
            self.ticket_id = ticket.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_ticket_unauthorized(self):
        resp = self.client.post(
            '/service_tickets/',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

    def test_create_ticket_success(self):
        payload = {
            'vin': 'VIN123',
            'service_date': '2025-04-22',
            'service_desc': 'Test',
            'customer_id': self.customer_id
        }
        resp = self.client.post(
            '/service_tickets/',
            data=json.dumps(payload),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn('id', resp.get_json())

    def test_get_tickets(self):
        resp = self.client.get('/service_tickets/')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('tickets', body)
        self.assertIn('meta', body)

    def test_update_ticket_success(self):
        payload = {'service_desc': 'Updated'}
        resp = self.client.put(
            f'/service_tickets/{self.ticket_id}',
            data=json.dumps(payload),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['service_desc'], 'Updated')

    def test_update_ticket_not_found(self):
        resp = self.client.put(
            '/service_tickets/999',
            data=json.dumps({'vin':'X'}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)

    def test_edit_ticket_mechanics_success(self):
        # add and then remove
        # first create another mech:
        with self.app.app_context():
            m2 = Mechanic(
                name='Two',
                email='two@ex.com',
                phone='555-2222',
                salary=30000,
                password=generate_password_hash('tpass')
            )
            db.session.add(m2)
            db.session.commit()
            other_id = m2.id

        # add
        resp1 = self.client.put(
            f'/service_tickets/{self.ticket_id}/edit',
            data=json.dumps({'add_ids':[other_id]}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp1.status_code, 200)

        # remove
        resp2 = self.client.put(
            f'/service_tickets/{self.ticket_id}/edit',
            data=json.dumps({'remove_ids':[other_id]}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp2.status_code, 200)

    def test_edit_ticket_mechanics_not_found_ticket(self):
        resp = self.client.put(
            '/service_tickets/999/edit',
            data=json.dumps({'add_ids':[self.mech_id]}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_ticket_success(self):
        resp = self.client.delete(
            f'/service_tickets/{self.ticket_id}',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_ticket_not_found(self):
        resp = self.client.delete(
            '/service_tickets/999',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
