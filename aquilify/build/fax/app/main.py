SCHEMATIC = """from aquilify.core.schematic import Schematic

# Schematic is a dynamic routing for Aquilify,
# You can use it part the routing in diffent octant :: @refer -> 3691

dynamicview = Schematic("my dynamic schematic") # Create a varible define the Schematic class and pass the name to the class.

# Define all you views...

async def home() -> dict:
    ...

# add the views here..

dynamicview.add_rule('/', methods=['GET', 'POST'], endpoint=home)

# don't forgot to link the schematic with you main application,
# In constructor.py using link function importing from aquilify.core.routing"""