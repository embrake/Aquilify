from electrus.asynchronous import Electrus

client = Electrus()
database = client['curd-test']
collection = database['users']