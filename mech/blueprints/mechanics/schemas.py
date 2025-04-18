from marshmallow import fields
from ...extensions import ma
from ...models import Mechanic

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    tickets = fields.Nested("ServiceTicketSchema", many=True, dump_only=True)

    class Meta:
        model = Mechanic
        load_instance = False
        include_relationships = True
        fields = ("id", "name", "email", "phone", "salary", "password", "tickets")

mechanic_schema  = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)