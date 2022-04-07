import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import hmac
import hashlib
import json


class CryptoPayments():
    def __init__(self, publicKey, privateKey):
        self.publicKey = publicKey
        self.privateKey = privateKey
        self.format = 'json'
        self.version = 1
        self.url = 'https://www.coinpayments.net/api.php'

    def createHmac(self, **params):
        """ Generate an HMAC based upon the url arguments/parameters
            We generate the encoded url here and return it to Request because
            the hmac on both sides depends upon the order of the parameters, any
            change in the order and the hmacs wouldn't match
        """
        encoded = urllib.parse.urlencode(params).encode('utf-8')
        return encoded, hmac.new(bytearray(self.privateKey, 'utf-8'),
                                 encoded, hashlib.sha512).hexdigest()

    def Request(self, request_method, **params):
        """ The basic request that all API calls use
            the parameters are joined in the actual api methods so the parameter
            strings can be passed and merged inside those methods instead of the
            request method. The final encoded URL and HMAC are generated here
        """
        encoded, sig = self.createHmac(**params)

        headers = {'hmac': sig}

        if request_method == 'get':
            req = urllib.request.Request(self.url, headers=headers)
        elif request_method == 'post':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            req = urllib.request.Request(self.url, data=encoded,
                                         headers=headers)

        try:
            response = urllib.request.urlopen(req)
            status_code = response.getcode()
            response_body = response.read()
            response_body_decoded = json.loads(response_body)

            response_body_decoded.update(response_body_decoded['result'])
            response_body_decoded.pop('result', None)
        except urllib.error.HTTPError as e:
            status_code = e.getcode()
            response_body = e.read()

        return response_body_decoded

    def createTransaction(self, params={}):
        """ Creates a transaction to give to the purchaser
            https://www.coinpayments.net/apidoc-create-transaction
        """
        params.update({'cmd': 'create_transaction',
                       'key': self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def getTransactionInfo(self, txid):
        """Get transaction info
                       https://www.coinpayments.net/apidoc-get-tx-info
        """
        params = {'cmd': 'get_tx_info',
                       'txid': txid,
                       'key': self.publicKey,
                       'version': self.version,
                       'format': self.format}
        return self.Request('post', **params)

    def rates(self, params={}):
        """Gets current rates for currencies
           https://www.coinpayments.net/apidoc-rates
        """
        params.update({'cmd': 'rates',
                       'key': self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)
