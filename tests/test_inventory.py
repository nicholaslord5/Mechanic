import unittest
import json
from datetime import date
from werkzeug.security import generate_password_hash
from mech import create_app
from mech.extensions import db
from mech.models import Inventory, Customer, Mechanic, ServiceTicket

class InventoryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            ##### seed customer, mechanic, ticket
            cust = Customer(
                name='C',
                email='c@ex.com',
                phone='555-3000',
                password=generate_password_hash('cp')
            )
            mech = Mechanic(
                name='M',
                email='m@ex.com',
                phone='555-4000',
                salary=40000,
                password=generate_password_hash('mp')
            )
            db.session.add_all([cust, mech])
            db.session.commit()
            self.customer_id = cust.id
            self.token = self.client.post(
                '/mechanics/login',
                data=json.dumps({'email':'m@ex.com','password':'mp'}),
                content_type='application/json'
            ).get_json()['auth_token']

            ticket = ServiceTicket(
                vin='VININV',
                service_date=date(2025, 4, 22),
                service_desc='Inv test',
                customer_id=self.customer_id
            )
            db.session.add(ticket)
            db.session.commit()
            self.ticket_id = ticket.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_part_unauthorized(self):
        resp = self.client.post(
            '/inventory/',
            data=json.dumps({'name':'X','price':1.23}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

    def test_create_part_success(self):
        resp = self.client.post(
            '/inventory/',
            data=json.dumps({'name':'Filter','price':9.99}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertIn('id', body)

    def test_get_parts(self):
        resp = self.client.get('/inventory/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_update_part_success(self):
        ###### create part first
        part = self.client.post(
            '/inventory/',
            data=json.dumps({'name':'F','price':5.55}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        ).get_json()
        resp = self.client.put(
            f"/inventory/{part['id']}",
            data=json.dumps({'price':7.77}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['price'], 7.77)

    def test_delete_part_success(self):
        part = self.client.post(
            '/inventory/',
            data=json.dumps({'name':'Y','price':2.22}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        ).get_json()
        resp = self.client.delete(
            f"/inventory/{part['id']}",
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(resp.status_code, 200)

    def test_add_part_to_ticket_success(self):
        part = self.client.post(
            '/inventory/',
            data=json.dumps({'name':'Z','price':3.33}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        ).get_json()
        resp = self.client.post(
            f"/inventory/{self.ticket_id}/add_part",
            data=json.dumps({'part_id': part['id']}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)

    def test_add_part_to_ticket_not_found(self):
        #### invalid ticket
        resp1 = self.client.post(
            "/inventory/999/add_part",
            data=json.dumps({'part_id': 1}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp1.status_code, 404)
        #### invalid part
        ####### first create ticket part ok, then wrong part_id
        self.client.post(
            '/inventory/',
            data=json.dumps({'name':'A','price':1.11}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        resp2 = self.client.post(
            f"/inventory/{self.ticket_id}/add_part",
            data=json.dumps({'part_id':999}),
            headers={'Authorization': f'Bearer {self.token}'},
            content_type='application/json'
        )
        self.assertEqual(resp2.status_code, 404)
    
    def test_update_part_not_found(self):
        resp = self.client.put(
        '/inventory/999',
        data=json.dumps({'price':9.99}),
        headers={'Authorization': f'Bearer {self.token}'},
        content_type='application/json'
    )
        self.assertEqual(resp.status_code, 404)

    def test_delete_part_not_found(self):
        resp = self.client.delete(
        '/inventory/999',
        headers={'Authorization': f'Bearer {self.token}'}
    )
        self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
