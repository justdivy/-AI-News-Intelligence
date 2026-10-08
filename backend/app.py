"""Flask API entry point for the AI News Intelligence project."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from nltk import sent_tokenize
from werkzeug.exceptions import HTTPException

from services.keywords import extract_keywords
from services.ner import extract_entities
from services.pos_tagger import tag_parts_of_speech
from services.preprocessing import preprocess_text
from services.statistics import analyze_word_frequency
from services.summarizer import summarize_text


MAX_ARTICLE_CHARACTERS = 50_000
MAX_REQUEST_BYTES = 2_000_000


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    # The frontend is static during development; restrict browser access to local origins.
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://127.0.0.1:5500",
                    "http://localhost:5500",
                    "http://127.0.0.1:8000",
                    "http://localhost:8000",
                ]
            }
        },
    )

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled request error")
        if request.path.startswith("/api/"):
            return jsonify({"error": "An unexpected server error occurred. Check the backend logs."}), 500
        return "An unexpected server error occurred.", 500

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "AI News Intelligence API",
                "status": "running",
                "health": "/api/health",
            }
        )

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "ai-news-intelligence"})

    @app.post("/api/analyze")
    def analyze_article():
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json."}), 415

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Send a JSON object containing an article 'text'."}), 400

        article = payload.get("text")
        if not isinstance(article, str):
            return jsonify({"error": "The article 'text' must be a string."}), 400
        if not article.strip():
            return jsonify({"error": "The article cannot be empty."}), 400
        if len(article) > MAX_ARTICLE_CHARACTERS:
            return jsonify(
                {"error": f"The article exceeds the {MAX_ARTICLE_CHARACTERS:,}-character limit."}
            ), 413

        try:
            preprocessing = preprocess_text(article)
            entities = extract_entities(article)
            keywords = extract_keywords(article)
            word_frequency = analyze_word_frequency(article)
            pos = tag_parts_of_speech(article)
            summary = summarize_text(article)
            sentence_count = len(sent_tokenize(article))
        except (LookupError, RuntimeError) as error:
            return jsonify({"error": str(error)}), 503
        except Exception:
            app.logger.exception("Article analysis failed")
            return jsonify({"error": "Analysis failed unexpectedly. Check the backend logs."}), 500

        words = [word for word in article.split() if any(character.isalnum() for character in word)]
        unique_words = {word.casefold() for word in words}

        return jsonify(
            {
                "statistics": {
                    "total_words": len(words),
                    "unique_words": len(unique_words),
                    "sentences": sentence_count,
                    "entities": entities["entity_count"],
                    "keywords": len(keywords["keywords"]),
                },
                "preprocessing": preprocessing,
                "entities": entities,
                "keywords": keywords,
                "word_frequency": word_frequency,
                "pos": pos,
                "summary": summary,
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
