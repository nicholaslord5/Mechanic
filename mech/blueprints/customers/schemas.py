from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.extensions import ma
from mech.models import Customer

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    password = fields.String(load_only=True, required=True)

    class Meta:
        model = Customer
        load_instance = False
        include_fk = True
        fields = ("id", "name", "email", "phone", "password")

customer_schema  = CustomerSchema()
customers_schema = CustomerSchema(many=True)