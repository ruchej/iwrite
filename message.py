import json

from decorators import Log
from settings import ENCODING, MAX_PACKAGE_LENGTH


class Message:
    @Log()
    def get(self, client):
        """
        Method of receiving and decoding a message
        accepts bytes gives a dictionary if something else is received gives an error value
        """

        encoded_response = client.recv(MAX_PACKAGE_LENGTH)
        if isinstance(encoded_response, bytes):
            json_response = encoded_response.decode(ENCODING)
            response = json.loads(json_response)
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError

    @Log()
    def send(self, sock, message):
        """
        Method of message encoding and sending
        accepts the dictionary and sends it
        """

        js_message = json.dumps(message)
        encoded_message = js_message.encode(ENCODING)
        sock.send(encoded_message)
