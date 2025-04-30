from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.extensions import ma
from mech.models import Inventory

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        load_instance = False
        include_fk = True
        fields = ("id", "name", "price")

inventory_schema   = InventorySchema()
inventories_schema = InventorySchema(many=True)
