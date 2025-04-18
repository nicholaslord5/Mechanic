from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.models import Customer
from mech.extensions import ma
from marshmallow import fields

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    password = fields.String(load_only=True, required=True)
    
    class Meta:
        model = Customer
        fields = ('name', 'email', 'phone', 'id', 'password')
        load_instance = False
        include_fk = True

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)