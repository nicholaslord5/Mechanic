from datetime import date
from marshmallow import fields, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.models import ServiceTicket
from mech.blueprints.mechanics.schemas import MechanicSchema  # import the class

class ServiceDateField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                return date(*value)
            except Exception:
                raise ValidationError("Invalid date tuple, expected [YYYY, M, D].")
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except Exception:
                raise ValidationError("Invalid date string, expected YYYY-MM-DD.")
        if isinstance(value, date):
            return value
        raise ValidationError("Unsupported date format.")

class ServiceTicketSchema(SQLAlchemyAutoSchema):
    ###### use custom field to parse date strings/tuples #####
    service_date = ServiceDateField(required=True)

    ###### nest only id and for mechanics #####
    mechanics = fields.Nested(
        MechanicSchema,
        only=("id", "name"),
        many=True,
        dump_only=True
    )

    class Meta:
        model = ServiceTicket
        load_instance = False
        include_fk = True
        fields = (
            "id",
            "vin",
            "service_date",
            "service_desc",
            "customer_id",
            "mechanics",
        )

service_ticket_schema  = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
