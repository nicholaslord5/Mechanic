from datetime import date
from marshmallow import fields, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.extensions import ma
from mech.models import Mechanic

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    #### Avoiding re-nest of each ticket’s mechanics to kill endless loop
    tickets = fields.Nested(
        "mech.blueprints.service_tickets.schemas.ServiceTicketSchema",
        many=True,
        dump_only=True,
        exclude=("mechanics",)
    )
    password = fields.String(load_only=True)

    class Meta:
        model = Mechanic
        load_instance = False
        include_fk = True
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "salary",
            "password",
            "tickets",
        )

mechanic_schema  = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)
