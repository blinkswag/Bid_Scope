#token_manager.py

import time
import requests
import logging

logger = logging.getLogger(__name__)

class ZohoDeskTokenManager:
    def __init__(self, db):
        self.db = db
        self.collection = db.Zoho_desk_ticket
        self.token_data = self.collection.find_one(sort=[('_id', -1)])  # Get the latest token data
        logger.debug(f"Token data from database: {self.token_data}")

    def get_access_token(self):
        if not self.token_data:
            raise Exception("No token data found in the database")

        current_time = int(time.time())
        expires_in = self.token_data.get('expires_in', 0)
        access_token = self.token_data.get('access_token', None)

        logger.debug(f"Current time: {current_time}, expires_in: {expires_in}, access_token: {access_token}")

        # If the token will expire in less than 5 minutes or has already expired, refresh it
        if access_token and (expires_in - current_time > 300):
            return access_token
        else:
            return self.refresh_access_token()

    def refresh_access_token(self):
        refresh_token = self.token_data.get('refresh_token')
        client_id = self.token_data.get('client_id')
        client_secret = self.token_data.get('client_secret')

        if not refresh_token:
            logger.error("Missing refresh_token in token data")
        if not client_id:
            logger.error("Missing client_id in token data")
        if not client_secret:
            logger.error("Missing client_secret in token data")

        if not refresh_token or not client_id or not client_secret:
            raise Exception("Missing required token data for refresh")

        token_response = requests.post(
            "https://accounts.zoho.com/oauth/v2/token",
            data={
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': 'https://zoho.com/desk'
            }
        )

        if not token_response.ok:
            logger.error(f"Failed to refresh access token: {token_response.text}")
            raise Exception("Failed to refresh access token")

        token_data = token_response.json()
        access_token = token_data['access_token']
        expires_in = int(time.time()) + token_data['expires_in']

        logger.debug(f"New access token: {access_token}, expires_in: {expires_in}")

        # Update the existing document with the new access token and expiry time
        new_token_data = {
            'access_token': access_token,
            'expires_in': expires_in,
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }

        # Update the existing token entry
        self.collection.update_one(
            {'_id': self.token_data['_id']},
            {'$set': new_token_data}
        )

        # Update the current token data reference
        self.token_data = new_token_data

        return access_token
