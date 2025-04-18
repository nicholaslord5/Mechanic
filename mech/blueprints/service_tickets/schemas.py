from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.models import ServiceTicket
from mech.extensions import ma
from marshmallow import fields

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    mechanics = fields.Nested('MechanicSchema', many=True, dump_only=True)
    
    class Meta:
        model = ServiceTicket
        fields = ('id', 'vin', 'service_date', 'service_desc', 'customer_id', 'mechanics')
        load_instance = False
        include_fk = True

ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)