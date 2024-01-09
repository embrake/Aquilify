from aquilify.orm.sqlite3 import Table

from aquilify.orm.fields import PrimaryKeyField, VarCharField, IntegerField

class User(Table):
    __tablename__ = 'users'
    
    id = PrimaryKeyField( )
    ssid = IntegerField(  )
    name = VarCharField( max_length = 255 )
    email = VarCharField( max_length = 255 )
    password = VarCharField( max_length = 255 )
    
