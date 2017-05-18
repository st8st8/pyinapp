import json
from datetime import datetime
from arrow.parser import DateTimeParser
from httplib2 import Http

from oauth2client.service_account import ServiceAccountCredentials
from pytz import utc


class Purchase(object):

    def __init__(self, transaction_id, product_id, quantity, purchased_at, purchased_at_datetime, expires_date):
        self.transaction_id = transaction_id
        self.product_id = product_id
        self.quantity = quantity
        self.purchased_at = purchased_at
        self.purchased_at_datetime = purchased_at_datetime
        self.expires_date = expires_date

    @classmethod
    def from_app_store_receipt(cls, receipt, get_expiry=True):
        parser = DateTimeParser()
        purchase = {
            'transaction_id': receipt['transaction_id'],
            'product_id': receipt['product_id'],
            'quantity': receipt['quantity']
        }
        purchase["purchased_at_datetime"] = parser.parse(receipt["purchase_date"], "YYYY-MM-DD HH:mm:ss ZZZ")

        if 'expires_date' in receipt and get_expiry:
            try:
                purchase["expires_date"] = datetime.utcfromtimestamp(float(receipt["expires_date"])/1000)
            except ValueError:
                purchase["expires_date"] = parser.parse(receipt["expires_date"], "YYYY-MM-DD HH:mm:ss ZZZ")
        return cls(**purchase)

    @classmethod
    def from_google_play_receipt(cls, receipt, get_expiry=True, keyfile=None):
        purchase = {
            'transaction_id': receipt.get('orderId', receipt.get('purchaseToken')),
            'product_id': receipt['productId'],
            'quantity': 1,
            'purchased_at': receipt['purchaseTime'],
            'expires_date': None
        }
        purchase["purchased_at_datetime"] = datetime.utcfromtimestamp(float(receipt['purchaseTime'])/1000)

        if get_expiry:
            scope = "https://www.googleapis.com/auth/androidpublisher"
            credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scopes=[scope])
            http_auth = credentials.authorize(Http())
            sub = receipt["productId"]
            token = receipt["purchaseToken"]
            package = receipt["packageName"]
            url = "https://www.googleapis.com/androidpublisher/v2/applications/{0}/purchases/subscriptions/{1}/tokens/{2}"\
                .format(package, sub, token)
            response, content = http_auth.request(url)
            validation = json.loads(content)
            purchase["expires_date"] = datetime.utcfromtimestamp(float(validation["expiryTimeMillis"])/1000)
        return cls(**purchase)
