"""
Flask web site with vocabulary matching game
(identify vocabulary words that can be made
from a scrambled string)
"""

import flask
from flask import request, jsonify
import logging

# Our modules
from src.letterbag import LetterBag
from src.vocab import Vocab
from src.jumble import jumbled
import src.config as config


###
# Globals
###
app = flask.Flask(__name__)

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY  # Should allow using session variables

#
# One shared 'Vocab' object, read-only after initialization,
# shared by all threads and instances.  Otherwise we would have to
# store it in the browser and transmit it on each request/response cycle,
# or else read it from the file on each request/responce cycle,
# neither of which would be suitable for responding keystroke by keystroke.

WORDS = Vocab(CONFIG.VOCAB)
SEED = CONFIG.SEED
try:
    SEED = int(SEED)
except ValueError:
    SEED = None


###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
    """The main page of the application"""
    flask.g.vocab = WORDS.as_list()
    flask.session["target_count"] = min(
        len(flask.g.vocab), CONFIG.SUCCESS_AT_COUNT)
    flask.session["jumble"] = jumbled(
        flask.g.vocab, flask.session["target_count"], seed=None if not SEED or SEED < 0 else SEED)
    flask.session["matches"] = []
    app.logger.debug("Session variables have been set")
    assert flask.session["matches"] == []
    assert flask.session["target_count"] > 0
    app.logger.debug("At least one seems to be set correctly")
    return flask.render_template('vocab.html')


@app.route("/keep_going")
def keep_going():
    """
    After initial use of index, we keep the same scrambled
    word and try to get more matches
    """
    flask.g.vocab = WORDS.as_list()
    return flask.render_template('vocab.html')


@app.route("/success")
def success():
    return flask.render_template('success.html')


#######################
# Form handler.
#######################
@app.route("/_check", methods=["GET", "POST"])
def check():
    """
    User has submitted a word ('attempt')
    """

    text = request.args.get("text", type=str)
    jumble = flask.session["jumble"]
    matches = flask.session.get("matches", [])  # Default to empty list

    in_jumble = LetterBag(jumble).contains(text)
    matched = WORDS.has(text)
    
    app.logger.debug(f"Current Text: {text}")
    app.logger.debug(f"Target Count: {flask.session['target_count']}")
    app.logger.debug(f"Current Matches: {flask.session['matches']}")
    app.logger.debug(f"Length of Matches: {len(matches)}")

    if matched and in_jumble and not (text in matches):
        matches.append(text)
        flask.session["matches"] = matches

        if len(matches) >= flask.session["target_count"]:
            app.logger.debug(f"Success!")
            return flask.jsonify(result={"status": "success"})

        return flask.jsonify(result={"status": "keep_going", "word": text})

    elif text in matches:
        return flask.jsonify(result={"status": "error", "message": "You already found {}".format(text)})
    elif not matched:
        return flask.jsonify(result={"status": "error", "message": "{} isn't in the list of words".format(text)})
    elif not in_jumble:
        return flask.jsonify(result={"status": "error", "message": '"{}" can\'t be made from the letters {}'.format(text, jumble)})
    else:
        app.logger.debug("This case shouldn't happen!")
        assert False  # Raises AssertionError

    if len(matches) >= flask.session["target_count"]:
        app.logger.debug(f"Success!")
        return flask.jsonify(result={"status": "success"})
    else:
        return flask.jsonify(result={"status": "keep_going", "message": "Your error or success message here"})


###############
# AJAX request handlers
#   These return JSON, rather than rendering pages.
###############

@app.route("/_example")
def example():
    """
    Example ajax request handler
    """
    app.logger.debug("Got a JSON request")
    rslt = {"key": "value"}
    return flask.jsonify(result=rslt)


#################
# Functions used within the templates
#################

@app.template_filter('filt')
def format_filt(something):
    """
    Example of a filter that can be used within
    the Jinja2 code
    """
    return "Not what you asked for"

###################
#   Error handlers
###################


@app.errorhandler(404)
def error_404(e):
    app.logger.warning("++ 404 error: {}".format(e))
    return flask.render_template('404.html'), 404


@app.errorhandler(500)
def error_500(e):
    app.logger.warning("++ 500 error: {}".format(e))
    assert not True  # I want to invoke the debugger
    return flask.render_template('500.html'), 500


@app.errorhandler(403)
def error_403(e):
    app.logger.warning("++ 403 error: {}".format(e))
    return flask.render_template('403.html'), 403


#############

if __name__ == "__main__":
    if CONFIG.DEBUG:
        app.debug = True
        app.logger.setLevel(logging.DEBUG)
        app.logger.info(
            "Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=5002, host="0.0.0.0", debug=CONFIG.DEBUG)
