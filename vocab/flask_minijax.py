"""
Demo of an AJAX interaction
"""

import flask
from flask import request
import logging

# Our modules
import src.config as config


###
# Globals
###
app = flask.Flask(__name__)

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY  # Sign my cookies


###
# Pages
###

@app.route("/")
def index():
    return flask.render_template('minijax.html')


###############
# AJAX request handlers
#   These return JSON to JQuery, and it updates the webpage,
#   as opposed to rendering a new page.
###############

@app.route("/_countem")
def countem():
    text = request.args.get("text", type=str)
    length = len(text)
    rslt = {"long_enough": length >= 5}
    return flask.jsonify(result=rslt)


#############

if __name__ == "__main__":
    if CONFIG.DEBUG:
        app.debug = True
        app.logger.setLevel(logging.DEBUG)
        app.logger.info("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0", debug=CONFIG.DEBUG)
