import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.app import create_app


class HistoryDeleteCorsTest(unittest.TestCase):
    def test_delete_preflight_allows_delete_method(self):
        app = create_app()

        client = app.test_client()
        response = client.open(
            "/api/games/1",
            method="OPTIONS",
            headers={
                "Origin": "http://127.0.0.1:4173",
                "Access-Control-Request-Method": "DELETE",
            },
        )

        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        self.assertIn("DELETE", allow_methods)


if __name__ == "__main__":
    unittest.main()
