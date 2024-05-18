from flask import Flask, redirect, request, make_response
import requests, uuid
from urllib.parse import quote_plus

from .secrets import client_id, client_secret

app = Flask(__name__)

redirect_uri = "http://localhost:5000/callback"
redirect_uri_urlencoded = quote_plus(redirect_uri)

@app.route("/link", methods=["GET", "POST"])
def link():
    if request.method == 'POST':
        state = str(uuid.uuid4()) # better way ?
        response = make_response(redirect(f'https://discord.com/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri_urlencoded}&scope=identify&state={state}'))
        response.set_cookie('oauth2_state', state, httponly=True, samesite='Lax')
        return response
    elif request.method == 'GET':
        return '<form method="POST"><input type="submit" value="Link Discord"></form>'

@app.route("/callback")
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    validate_state = request.cookies.get('oauth2_state')
    if state != validate_state:
        return 403, "Denied."

    auth = (client_id, client_secret)
    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code
    }
    r = requests.post('https://discord.com/api/oauth2/token', data=data, auth=auth)
    token = r.json().get('access_token')
    r2 = requests.get('https://discordapp.com/api/users/@me', headers={'Authorization': f'Bearer {token}'})
    discord_id = r2.json().get('id')
    username = r2.json().get('username')
    r3 = requests.post('https://discord.com/api/oauth2/token/revoke', data={'token': token, 'token_type_hint': 'access_token'}, auth=auth)
    
    response = make_response(f"successfully linked discord user {username} with id {discord_id}")
    response.set_cookie('oauth2_state', '', expires=0)
    return response
