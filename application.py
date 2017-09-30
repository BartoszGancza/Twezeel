from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_jsglue import JSGlue
from twython import Twython, TwythonAuthError, TwythonError, TwythonRateLimitError
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
import html
import plotly as py
import plotly.graph_objs as go


# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# config for filesystem session
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'app secret key'
Session(app)
JSGlue(app)

# Twitter app keys
APP_KEY = 'Twitter app key'
APP_SECRET = 'Twitter app secret key'


@app.route('/', methods=["GET", "POST"])
def index():

    if request.method == "POST":

        # base instance for OAuth2 (app based authentication), nothing more necessary
        twitterOAuth2 = Twython(APP_KEY, APP_SECRET, oauth_version=2)
        session["ACCESS_TOKEN"] = twitterOAuth2.obtain_access_token()
        session["twitterOAuth2"] = Twython(APP_KEY, access_token=session["ACCESS_TOKEN"])

        # base instance for OAuth1.1 (user based authentication), process finished by handling callback url in /login
        twitter = Twython(APP_KEY, APP_SECRET)
        auth = twitter.get_authentication_tokens(callback_url='full url/login')
        # temporary tokens (as required by the method)
        session['OAUTH_TOKEN'] = auth['oauth_token']
        session['OAUTH_TOKEN_SECRET'] = auth['oauth_token_secret']
        return redirect(auth['auth_url'])
    else:
        return render_template('index.html')

@app.route('/login')
def login():

    # rest of authentication process
    oauth_verifier = request.args.get('oauth_verifier')
    OAUTH_TOKEN=session['OAUTH_TOKEN']
    OAUTH_TOKEN_SECRET=session['OAUTH_TOKEN_SECRET']
    # temporary middle instance for receiving final tokens
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    final_step = twitter.get_authorized_tokens(oauth_verifier)
    session['OAUTH_TOKEN'] = final_step['oauth_token']
    session['OAUTH_TOKEN_SECRET'] = final_step['oauth_token_secret']
    OAUTH_TOKEN = session['OAUTH_TOKEN']
    OAUTH_TOKEN_SECRET = session['OAUTH_TOKEN_SECRET']

    # final instance to be used app-wide for user authenticated operations (Tweeting, DMs, etc.)
    session['twitter'] = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    # get all user data of authenticated user for session log-in and app-wide use
    session['screen_name'] = session['twitter'].verify_credentials()
    session["dm"] = []
    session["tweets_embed"] = []
    session["mentions"] = []
    session["followers"] = []

    flash("You've logged in!")
    return redirect('/')

@app.route('/logout')
def logout():

    # clear the session logging out the user and render the log in page
    session.clear()

    flash("You've been successfuly logged out!")
    return render_template('index.html')

@app.route('/followers')
def followers():

    if not session["followers"]:
        try:
            session["followers"] = session["twitterOAuth2"].get_followers_list(user_id = session["screen_name"]["id"], count=30)["users"]
            return jsonify(session["followers"])
        except (TwythonError, TwythonAuthError, TwythonRateLimitError) as error:
            flash(error)
            return render_template("index.html")

    else:
        return jsonify(session["followers"])


@app.route("/get_tweets")
def get_tweets():

    if not session["tweets_embed"]:
        try:
            tweets = session["twitterOAuth2"].get_user_timeline(user_id = session["screen_name"]["id"], count = 10)
        except (TwythonError, TwythonAuthError, TwythonRateLimitError) as error:
            flash(error)
            return render_template("index.html")
        else:

            # APIs built in embedding mechanism (produces nice HTML to embed a Tweet on the website)
            # there is probably a simpler way to grab the URL for oembed, but I'm too tired to figure that out -_-
            for tweet in tweets:
                link = "https://twitter.com/" + session["screen_name"]["screen_name"] + "/status/" + tweet["id_str"]
                session["tweets_embed"].append(session["twitterOAuth2"].get_oembed_tweet(url = link)["html"])

            return jsonify(session["tweets_embed"])

    else:
        return jsonify(session["tweets_embed"])

@app.route("/get_mentions")
def get_mentions():

    if not session["mentions"]:
        try:
            mentions = session["twitter"].get_mentions_timeline(count = 10)
        except (TwythonError, TwythonAuthError, TwythonRateLimitError) as error:
            flash(error)
            return render_template("index.html")
        else:

            # APIs built in embedding mechanism (produces nice HTML to embed a Tweet on the website)
            # there is probably a simpler way to grab the URL for oembed, but I'm too tired to figure that out -_-
            for mention in mentions:
                link = "https://twitter.com/" + mention["user"]["screen_name"] + "/status/" + mention["id_str"]
                session["mentions"].append(session["twitterOAuth2"].get_oembed_tweet(url = link)["html"])

            return jsonify(session["mentions"])

    else:
        return jsonify(session["mentions"])

@app.route("/get_dm")
def get_dm():

    if not session["dm"]:
        try:
            session["dm"] = session["twitter"].get_direct_messages()
            return jsonify(session["dm"])
        except (TwythonError, TwythonAuthError, TwythonRateLimitError) as error:
            flash(error)
            return render_template("index.html")

    else:
        return jsonify(session["dm"])

@app.route("/overview", methods=["POST", "GET"])
def overview():

    if request.method == "POST":

        who = request.form.get("who")

        time = { "01":0, "02":0, "03":0, "04":0, "05":0, "06":0, "07":0, "08":0, "09":0, "10":0, "11":0, "12":0, "13":0, "14":0,
        "15":0, "16":0, "17":0, "18":0, "19":0, "20":0, "21":0, "22":0, "23":0, "00":0 }

        try:
            session["user_lookup"] = session['twitter'].lookup_user(screen_name=who)
            session["lookup_timeline"] = session['twitter'].get_user_timeline(screen_name=who, count=100, include_rts=1)
        except (TwythonError, TwythonAuthError, TwythonRateLimitError) as error:
            flash(error)
            return render_template("index.html")
        else:

            for tweet in session["lookup_timeline"]:
                hour = tweet["created_at"][11:-17]
                time[hour] += 1

            amount_of_tweets = []
            for key in time:
                amount_of_tweets.append(time[key])

            data = [go.Bar(
                x=["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14",
                "15", "16", "17", "18", "19", "20", "21", "22", "23", "00"],
                y=amount_of_tweets,
                hoverinfo="y"
                )]

            layout = go.Layout(
                plot_bgcolor="rgba(0, 0, 0, 0)",
                margin=dict(l=0,r=0,t=0,b=20,autoexpand=False),
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(visible=False, fixedrange=True),
                xaxis=dict(tickfont=dict(color="#c8c8c8"), fixedrange=True, tickmode="linear"),
                height=150
            )

            fig = go.Figure(data=data, layout=layout)
            chart = py.offline.plot(fig, output_type="div", show_link=False, link_text=False, config={"displayModeBar": False})
            utctime_now = str(datetime.utcnow())[11:-10]

            return render_template("overview.html", chart=chart, time=utctime_now)

    else:
        return render_template("overview.html")

@app.route("/tweet", methods=["POST"])
def tweet():

    if request.method == "POST":

        status_text = request.form.get("tweet")

        try:
            session["twitter"].update_status(status=html.unescape(status_text))
        except (TwythonError, TwythonAuthError, TwythonRateLimitError) as error:
            flash(error)
            return render_template("index.html")
        else:
            session["tweets_embed"] = []

            flash("You tweeted sucesfully!")
            return redirect("/")
