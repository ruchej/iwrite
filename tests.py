import unittest
import settings as s
from server import create_socket, client_message_handler


class TestServer(unittest.TestCase):
    err_dict = {s.KEY_RESPONSE: 400, s.KEY_ERROR: "Bad Request"}
    ok_dict = {s.KEY_RESPONSE: 200}

    def test_client_message_handler(self):
        msg = {
            s.KEY_ACTION: "presence",
            s.KEY_TIME: 1.1,
            s.KEY_USER: {"account_name": "Guest"},
        }
        self.assertEqual(client_message_handler(msg), self.ok_dict)

    def test_client_message_handler_action(self):
        msg = {
            s.KEY_TIME: 1.1,
            s.KEY_USER: {"account_name": "Guest"},
        }
        self.assertEqual(client_message_handler(msg), self.ok_dict)


if __name__ == "__main__":
    unittest.main()
