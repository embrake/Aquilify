# ROOT PIPELINE: @noql -> 3691
# Reference: http://aquilify.vvfin.in/pipeline/root

# Warning: Avoid altering this __root__.py file; it serves as the main tunnel for your application.
# To prevent pipeline errors, refrain from interfering with or renaming this file.

from aquilify.core import Aquilify

# Importing the core project of Aquilify.

__instance__ = Aquilify()

# Warning: If using uvicorn or other ASGI Servers, refrain from using __file__ or __instance__ to run the server.
# Import 'importer' from aquilify.settings.core import importer.
# Define a variable for your instance, e.g., app = importer().
# Assuming you have a file named main.py, run your application:
# `$ uvicorn main:app`
# Uvicorn will execute your application with all necessary resources.
# Ensure all routes are defined inside views.py and aquilify settings already configured to avoid potential errors or NotFound issues.

# Warning: Changing the default __instance__ name might lead to pipeline errors. Maintain the default naming convention to prevent issues.

# Visit http://aquilify.vvfin.in/pipeline/study for comprehensive information on customizing or modifying the pipeline.

# For further assistance, contact us at control@vvfin.in or confict.con@gmail.com.

# This __root__ file is a component of the Aquilify project governed by the BSD-4 Clause LICENSE.
