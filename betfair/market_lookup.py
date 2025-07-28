import requests
import logging

class BetfairMarketLookup:
    MARKET_CATALOGUE_URL = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"

    def __init__(self, app_key, session_token):
        self.app_key = app_key
        self.session_token = session_token

    def find_market_and_selection(self, market_filter, horse_name):
        headers = {
            'X-Application': self.app_key,
            'X-Authentication': self.session_token,
            'Content-Type': 'application/json'
        }

        params = {
            "filter": market_filter,
            "maxResults": "10",
            "marketProjection": ["RUNNER_METADATA"]
        }

        try:
            response = requests.post(self.MARKET_CATALOGUE_URL, headers=headers, json=params)
            data = response.json()

            for market in data:
                for runner in market.get("runners", []):
                    if runner["runnerName"].lower() == horse_name.lower():
                        return {
                            "market_id": market["marketId"],
                            "selection_id": runner["selectionId"]
                        }

            return {"error": f"Horse '{horse_name}' not found in available markets."}
        except Exception as e:
            logging.exception("Error fetching market data from Betfair")
            return {"error": str(e)}
