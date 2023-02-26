# Imports necessary libraries
import os
from flask import Flask
from flask_cors import CORS
from src.routes import api

# flask app setup

app = Flask(__name__) # initializes flask application
app.url_map.strict_slashes = False # doesn't require a slash at the end of the URL

app.register_blueprint(api, url_prefix="/api/v1") # actually apply the prefix to the bp

CORS(app, resources={r"*": {"origins": "*"}}) # prevents most CORS issues


# If the file is run directly,start the app.
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

# To execute, run the file. Then go to 127.0.0.1:5000 in your browser and look at a welcoming message.