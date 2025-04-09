from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.models import ServiceTicket
from mech.extensions import ma

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket
        fields = ('id', 'vin', 'service_date', 'service_desc', 'customer_id')
        load_instance = False
        include_fk = True

ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)