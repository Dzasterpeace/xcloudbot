# routes/betfair_oauth.py

from flask import Blueprint, redirect, request, jsonify
from auth_helpers import token_required
from extensions import db
from models import User
import os
import requests
from flasgger.utils import swag_from
from datetime import datetime, timedelta

oauth_bp = Blueprint('betfair_oauth', __name__, url_prefix='/betfair')

# Environment vars
CLIENT_ID     = os.getenv("BETFAIR_CLIENT_ID")
CLIENT_SECRET = os.getenv("BETFAIR_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("BETFAIR_REDIRECT_URI")

AUTH_URL  = "https://identitysso.betfair.com/oauth2/authorize"
TOKEN_URL = "https://identitysso.betfair.com/oauth2/token"

@oauth_bp.route('/oauth-url', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Betfair'],
    'summary': 'Get Betfair authorization URL',
    'description': 'Returns the URL your frontend should redirect the user to, in order to initiate OAuth2 login with Betfair.',
    'responses': {
        200: {
            'description': 'Authorization URL',
            'schema': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string'}
                }
            }
        }
    }
})
def get_oauth_url(current_user):
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI
    }
    url = AUTH_URL + '?' + '&'.join(f"{k}={requests.utils.quote(v)}" for k,v in params.items())
    return jsonify({'url': url})

@oauth_bp.route('/callback', methods=['GET'])
@token_required
def handle_callback(current_user):
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400

    # Exchange code for tokens
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    try:
        resp = requests.post(
            TOKEN_URL,
            data=data,
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        token_data = resp.json()
    except Exception as e:
        return jsonify({'error': 'Token exchange failed', 'details': str(e)}), 502

    if 'access_token' not in token_data:
        return jsonify({'error': 'Failed to retrieve tokens', 'details': token_data}), 400

    # Persist tokens (you’ll want to encrypt these!)
    current_user._betfair_access_token  = token_data['access_token']
    current_user._betfair_refresh_token = token_data['refresh_token']
    current_user.betfair_token_expiry   = datetime.utcnow() + timedelta(seconds=int(token_data['expires_in']))
    db.session.commit()

    return jsonify({'message': 'Betfair account successfully connected via OAuth2'}), 200

@oauth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    if not current_user._betfair_refresh_token:
        return jsonify({'error': 'No refresh token stored'}), 400

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': current_user._betfair_refresh_token
    }
    try:
        resp = requests.post(
            TOKEN_URL,
            data=data,
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        tok = resp.json()
    except Exception as e:
        return jsonify({'error': 'Refresh request failed', 'details': str(e)}), 502

    if 'access_token' not in tok:
        return jsonify({'error': 'Failed to refresh token', 'details': tok}), 400

    current_user._betfair_access_token  = tok['access_token']
    current_user._betfair_refresh_token = tok.get('refresh_token', current_user._betfair_refresh_token)
    current_user.betfair_token_expiry   = datetime.utcnow() + timedelta(seconds=int(tok['expires_in']))
    db.session.commit()

    return jsonify({'message': 'Betfair token refreshed'}), 200

@oauth_bp.route('/disconnect', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Betfair'],
    'summary': 'Unlink Betfair account',
    'responses': {
        200: {'description': 'Betfair account disconnected'},
        500: {'description': 'Error during unlink'}
    }
})
def disconnect(current_user):
    try:
        for attr in [
            '_betfair_access_token', '_betfair_refresh_token',
            'betfair_token_expiry'
        ]:
            setattr(current_user, attr, None)
        db.session.commit()
        return jsonify({'message': 'Betfair account disconnected'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
