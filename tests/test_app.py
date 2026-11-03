import os
import unittest
from unittest.mock import Mock, patch


_test_environment = patch.dict(
    os.environ,
    {
        "PYTHON_DOTENV_DISABLED": "1",
        "GROQ_API_KEY": "",
        "OPENAI_API_KEY": "",
        "QDRANT_URL": "",
        "QDRANT_API_KEY": "",
    },
)
_test_environment.start()
with patch("qdrant_client.QdrantClient"):
    import app as chatbot_app
_test_environment.stop()


class ChatRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = chatbot_app.app.test_client()
        self.chain_patch = patch.object(chatbot_app, "rag_chain", None)
        self.chain_patch.start()
        self.addCleanup(self.chain_patch.stop)

    def test_home_page_renders_chat_interface(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Medical Chatbot", response.data)

    def test_health_is_liveness_and_reports_rag_readiness(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "rag_ready": False})

    def test_readiness_fails_when_rag_is_not_configured(self):
        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"status": "not_ready"})

    def test_chat_requires_a_nonblank_question(self):
        response = self.client.post("/get", data={"msg": "  "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, "text/plain")

    def test_chat_rejects_questions_over_the_limit(self):
        response = self.client.post(
            "/get",
            data={"msg": "x" * (chatbot_app.MAX_QUESTION_LENGTH + 1)},
        )

        self.assertEqual(response.status_code, 400)

    def test_chat_rejects_oversized_request_body(self):
        response = self.client.post("/get", data={"msg": "x" * 9000})

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.mimetype, "text/plain")

    def test_standby_response_is_plain_text_and_does_not_expose_details(self):
        with patch.object(chatbot_app, "init_status", "Standby: private configuration"):
            with patch.object(chatbot_app, "init_error", "private exception"):
                response = self.client.post("/get", data={"msg": "test question"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertNotIn(b"private", response.data)

    def test_model_answer_is_returned_as_plain_text(self):
        chain = Mock()
        chain.invoke.return_value = {"answer": "<script>alert(1)</script>"}
        with patch.object(chatbot_app, "rag_chain", chain):
            response = self.client.post("/get", data={"msg": "test question"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.get_data(as_text=True), "<script>alert(1)</script>")

    def test_model_failure_returns_safe_error_without_logging_question(self):
        chain = Mock()
        chain.invoke.side_effect = RuntimeError("private provider details")
        with patch.object(chatbot_app, "rag_chain", chain):
            with self.assertLogs(chatbot_app.logger, level="ERROR") as captured:
                response = self.client.post("/get", data={"msg": "synthetic private question"})

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private provider details", response.get_data(as_text=True))
        self.assertNotIn("synthetic private question", "\n".join(captured.output))

    def test_chat_route_rejects_get(self):
        response = self.client.get("/get")

        self.assertEqual(response.status_code, 405)

    def test_readiness_passes_when_rag_is_configured(self):
        with patch.object(chatbot_app, "rag_chain", Mock()):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ready"})

    def test_allowed_frontend_origin_receives_cors_header(self):
        response = self.client.get(
            "/health",
            headers={"Origin": "https://chatbot-887c5.web.app"},
        )

        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "https://chatbot-887c5.web.app",
        )

    def test_unlisted_origin_does_not_receive_cors_header(self):
        response = self.client.get(
            "/health",
            headers={"Origin": "https://unlisted.example"},
        )

        self.assertNotIn("Access-Control-Allow-Origin", response.headers)


if __name__ == "__main__":
    unittest.main()
