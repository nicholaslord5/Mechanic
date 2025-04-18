from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from mech.models import Inventory
from mech.extensions import ma

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model        = Inventory
        include_fk   = True
        load_instance= False
        fields       = ("id", "name", "price")

inventory_schema  = InventorySchema()
inventories_schema = InventorySchema(many=True)