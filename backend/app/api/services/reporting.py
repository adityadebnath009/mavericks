import json
import os
from typing import List, Optional

import psycopg2

# ---------------------------------------------------------------------------
# Configuration — override via environment variables
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "orca"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
}

EMBEDDING_MODEL_NAME = os.getenv("REPORTING_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DEFAULT_TOP_K = int(os.getenv("REPORTING_TOP_K", "3"))

# Lazily-loaded singleton so importing this module doesn't pay the
# sentence-transformers load cost until it's actually needed.
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


class ReportingService:
    """
    Static-method service, called directly on the class:

        ReportingService.compile_report(cause="...")
    """

    # -----------------------------------------------------------------
    # Embedding
    # -----------------------------------------------------------------

    @staticmethod
    def embed_text(text: str) -> List[float]:
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text).__name__}")
        if not text.strip():
            raise ValueError("text must not be empty")
        model = _get_embedding_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    # -----------------------------------------------------------------
    # DB
    # -----------------------------------------------------------------

    @staticmethod
    def _connect():
        conn = psycopg2.connect(**DB_CONFIG)
        from pgvector.psycopg2 import register_vector
        register_vector(conn)
        return conn

    # -----------------------------------------------------------------
    # Corpus ingestion
    # -----------------------------------------------------------------

    @classmethod
    def ingest_corpus_file(cls, json_path: str) -> int:
        """
        Loads a JSON file of [{source, clause_id, text}, ...], embeds
        each entry's text, and inserts it into marine_safety_corpus.
        Returns the number of rows inserted.
        """
        if not os.path.isfile(json_path):
            raise ValueError(f"Corpus file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        if not isinstance(entries, list):
            raise TypeError("Corpus file must contain a JSON array of entries")

        inserted = 0
        with cls._connect() as conn:
            with conn.cursor() as cur:
                for entry in entries:
                    text = entry.get("text")
                    if not text:
                        continue
                    embedding = cls.embed_text(text)
                    cur.execute(
                        """
                        INSERT INTO marine_safety_corpus (source, clause_id, text, embedding)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (entry.get("source", "unknown"), entry.get("clause_id"), text, embedding),
                    )
                    inserted += 1
        return inserted

    # -----------------------------------------------------------------
    # Semantic search
    # -----------------------------------------------------------------

    @classmethod
    def semantic_search(cls, query_text: str, top_k: int = DEFAULT_TOP_K) -> List[dict]:
        """Returns the top_k most semantically similar corpus entries."""
        if not isinstance(query_text, str):
            raise TypeError(f"query_text must be a string, got {type(query_text).__name__}")
        if not query_text.strip():
            raise ValueError("query_text must not be empty")
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        query_embedding = cls.embed_text(query_text)

        with cls._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT source, clause_id, text,
                           1 - (embedding <=> %s) AS similarity
                    FROM marine_safety_corpus
                    ORDER BY embedding <=> %s
                    LIMIT %s;
                    """,
                    (query_embedding, query_embedding, top_k),
                )
                rows = cur.fetchall()

        return [
            {
                "source": r[0],
                "clause_id": r[1],
                "text": r[2],
                "similarity": round(float(r[3]), 3),
            }
            for r in rows
        ]

    # -----------------------------------------------------------------
    # Report compilation
    # -----------------------------------------------------------------

    @staticmethod
    def _format_cause(risk_factors: dict) -> str:
        """
        Turns a dict like:
            {"wave_height": {"value": 2.9, "limit": 2.5, "unit": "m", "label": "Significant Wave Height"}}
        into: "Significant Wave Height is predicted to reach 2.9 m, exceeding the safe limit of 2.5 m."

        This shape is a guess pending confirmation of what the Risk
        Assessment Agent actually hands off — adjust to match its real
        output once you can see it.
        """
        sentences = []
        for factor in risk_factors.values():
            label = factor.get("label", "Value")
            value = factor.get("value")
            limit = factor.get("limit")
            unit = factor.get("unit", "")
            if limit is not None:
                sentences.append(
                    f"{label} is predicted to reach {value}{unit}, exceeding the safe limit of {limit}{unit}."
                )
            else:
                sentences.append(f"{label}: {value}{unit}.")
        return " ".join(sentences)

    @classmethod
    def compile_report(
        cls,
        cause: Optional[str] = None,
        risk_factors: Optional[dict] = None,
        source_ref: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> dict:
        """
        Builds the explainable reasoning log: Cause + Regulatory
        Grounding + Source, matching the architecture doc's example
        format. Pass either a ready-made `cause` string, or a
        `risk_factors` dict to have one generated automatically.
        """
        if cause is None:
            if not risk_factors:
                raise ValueError("Either 'cause' or 'risk_factors' must be provided")
            cause = cls._format_cause(risk_factors)

        if not isinstance(cause, str) or not cause.strip():
            raise ValueError("cause must be a non-empty string")

        grounding = cls.semantic_search(cause, top_k=top_k)

        return {
            "cause": cause,
            "regulatory_grounding": grounding,
            "source_ref": source_ref,
            "reasoning_log": cls._render_reasoning_log(cause, grounding, source_ref),
        }

    @staticmethod
    def _render_reasoning_log(cause: str, grounding: List[dict], source_ref: Optional[str]) -> str:
        lines = [f"Cause: {cause}"]
        for g in grounding:
            clause = f" ({g['clause_id']})" if g.get("clause_id") else ""
            lines.append(f"Regulatory grounding — {g['source']}{clause}: \"{g['text']}\"")
        if source_ref:
            lines.append(f"Source: {source_ref}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick manual test — run `python services/reporting.py`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Assumes you've already run ingest_corpus_file() at least once.
    report = ReportingService.compile_report(
        cause="Significant Wave Height is predicted to reach 2.9 meters, exceeding your boat's safe limit of 2.5 meters.",
        source_ref="Buoy bay_of_bengal_15n90e",
    )
    print(json.dumps(report, indent=2))
