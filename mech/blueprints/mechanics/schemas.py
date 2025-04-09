from ...extensions import ma
from ...models import Mechanic

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = False
        fields = ("id", "name", "email", "phone", "salary")

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)