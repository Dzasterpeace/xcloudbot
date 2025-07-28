from flask import Blueprint, request, jsonify
from auth_helpers import token_required
from extensions import db
from models import User
from flasgger.utils import swag_from
import os
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta

users_bp = Blueprint('users', __name__, url_prefix='/users')

# Betfair OAuth2 endpoints & config
CLIENT_ID     = os.getenv("BETFAIR_CLIENT_ID")
CLIENT_SECRET = os.getenv("BETFAIR_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("BETFAIR_REDIRECT_URI")
AUTH_URL      = "https://identitysso.betfair.com/oauth2/authorize"
TOKEN_URL     = "https://identitysso.betfair.com/oauth2/token"

@users_bp.route('/betfair/oauth-url', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Users'],
    'summary': 'Get Betfair OAuth2 authorization URL',
    'responses': {
        200: {
            'description': 'The URL your frontend should redirect the user to',
            'schema': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string'}
                }
            }
        }
    }
})
def get_betfair_oauth_url(current_user):
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    return jsonify({'url': url})


@users_bp.route('/betfair/callback', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Users'],
    'summary': 'Handle Betfair OAuth2 callback',
    'parameters': [
        {
            'name': 'code',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Authorization code returned by Betfair'
        }
    ],
    'responses': {
        200: {'description': 'Betfair account successfully connected'},
        400: {'description': 'Missing or invalid code'},
        502: {'description': 'Token exchange failed'}
    }
})
def betfair_callback(current_user):
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400

    data = {
        'grant_type':    'authorization_code',
        'code':          code,
        'redirect_uri':  REDIRECT_URI
    }
    try:
        resp = requests.post(
            TOKEN_URL,
            data=urlencode(data),
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        tokens = resp.json()
    except Exception as e:
        return jsonify({'error': 'Token exchange failed', 'details': str(e)}), 502

    if 'access_token' not in tokens:
        return jsonify({'error': 'Failed to retrieve tokens', 'details': tokens}), 400

    # Persist (and encrypt) tokens & expiry
    current_user._betfair_access_token  = tokens['access_token']
    current_user._betfair_refresh_token = tokens['refresh_token']
    current_user.betfair_token_expiry   = datetime.utcnow() + timedelta(seconds=int(tokens['expires_in']))
    db.session.commit()

    return jsonify({'message': 'Betfair account connected via OAuth2'}), 200


@users_bp.route('/betfair/refresh', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Users'],
    'summary': 'Refresh Betfair access token',
    'responses': {
        200: {'description': 'Token refreshed'},
        400: {'description': 'No refresh token stored'},
        502: {'description': 'Refresh request failed'}
    }
})
def betfair_refresh(current_user):
    if not current_user._betfair_refresh_token:
        return jsonify({'error': 'No refresh token stored'}), 400

    data = {
        'grant_type':    'refresh_token',
        'refresh_token': current_user._betfair_refresh_token
    }
    try:
        resp = requests.post(
            TOKEN_URL,
            data=urlencode(data),
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        tok = resp.json()
    except Exception as e:
        return jsonify({'error': 'Refresh failed', 'details': str(e)}), 502

    if 'access_token' not in tok:
        return jsonify({'error': 'Failed to refresh token', 'details': tok}), 400

    current_user._betfair_access_token  = tok['access_token']
    current_user._betfair_refresh_token = tok.get('refresh_token', current_user._betfair_refresh_token)
    current_user.betfair_token_expiry   = datetime.utcnow() + timedelta(seconds=int(tok['expires_in']))
    db.session.commit()

    return jsonify({'message': 'Betfair access token refreshed'}), 200


@users_bp.route('/betfair/disconnect', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Users'],
    'summary': 'Unlink Betfair account',
    'responses': {
        200: {'description': 'Betfair account disconnected'},
        500: {'description': 'Error during unlinking'}
    }
})
def betfair_disconnect(current_user):
    try:
        # clear all Betfair‐related fields
        for attr in (
            '_betfair_access_token',
            '_betfair_refresh_token',
            'betfair_token_expiry'
        ):
            setattr(current_user, attr, None)
        db.session.commit()
        return jsonify({'message': 'Betfair account disconnected'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
