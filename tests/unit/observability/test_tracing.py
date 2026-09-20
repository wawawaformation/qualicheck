import base64
import json

import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from app.observability import tracing
from app.observability.tracing import JSONLSpanExporter


def test_jsonl_exporter_writes_one_line_per_span(tmp_path):
    output_path = tmp_path / "traces.jsonl"
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(str(output_path))))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("appel_llm_test") as span:
        span.set_attribute("duree_ms", 42)

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    trace_entry = json.loads(lines[0])
    assert trace_entry["name"] == "appel_llm_test"
    assert trace_entry["attributs"]["duree_ms"] == 42
    assert "trace_id" in trace_entry
    assert trace_entry["erreur"] is False


def test_jsonl_exporter_marks_error_status(tmp_path):
    output_path = tmp_path / "traces.jsonl"
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(str(output_path))))
    tracer = provider.get_tracer("test")

    from opentelemetry.trace import Status, StatusCode

    with tracer.start_as_current_span("appel_outil_test") as span:
        span.set_status(Status(StatusCode.ERROR, "echec simule"))

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    trace_entry = json.loads(lines[0])
    assert trace_entry["erreur"] is True


def test_langfuse_otlp_config_returns_endpoint_and_headers(monkeypatch):
    """Test que _langfuse_otlp_config retourne endpoint et headers corrects."""
    from app.observability.tracing import _langfuse_otlp_config

    # Test avec un URL avec trailing slash
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk_test_123")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk_test_456")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com/")

    endpoint, headers = _langfuse_otlp_config()

    # Vérifie que le endpoint est correct et que le trailing slash est supprimé.
    # OTLPSpanExporter(endpoint=...) prend la valeur telle quelle : c'est à
    # nous de viser le signal "traces" (/v1/traces), il ne l'ajoute que pour
    # la variable générique OTEL_EXPORTER_OTLP_ENDPOINT, qu'on n'utilise pas.
    assert endpoint == "https://cloud.langfuse.com/api/public/otel/v1/traces"

    # Vérifie que le header Authorization contient le bon base64
    assert "Authorization" in headers
    auth_header = headers["Authorization"]
    assert auth_header.startswith("Basic ")

    # Décode et vérifie le contenu
    decoded = base64.b64decode(auth_header[6:]).decode()
    assert decoded == "pk_test_123:sk_test_456"


def test_langfuse_otlp_config_raises_when_env_var_missing(monkeypatch):
    """Test que _langfuse_otlp_config lève ValueError si une env var manque."""
    from app.observability.tracing import _langfuse_otlp_config

    # Test avec LANGFUSE_PUBLIC_KEY manquant
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk_test_456")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com/")

    with pytest.raises(ValueError) as exc_info:
        _langfuse_otlp_config()
    assert "LANGFUSE_PUBLIC_KEY" in str(exc_info.value)
    assert "LANGFUSE_SECRET_KEY" in str(exc_info.value)
    assert "LANGFUSE_BASE_URL" in str(exc_info.value)


def test_jsonl_exporter_keeps_span_hierarchy_and_context(tmp_path):
    """La vue locale doit permettre de reconstituer l'arbre des spans.

    Sans `parent_span_id`, les horodatages et le `service_name`, le fichier
    n'est qu'un sac de spans plat : impossible de voir qu'un appel d'outil
    est un enfant de `repondre`, ni de les ordonner, ni de savoir quel
    service les a émis.
    """
    output_path = tmp_path / "traces.jsonl"
    provider = TracerProvider(resource=Resource.create({"service.name": "service-test"}))
    provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(str(output_path))))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("racine"):
        with tracer.start_as_current_span("enfant"):
            pass

    lignes = [json.loads(ligne) for ligne in output_path.read_text(encoding="utf-8").splitlines()]
    par_nom = {ligne["name"]: ligne for ligne in lignes}

    racine, enfant = par_nom["racine"], par_nom["enfant"]
    assert racine["parent_span_id"] is None
    assert enfant["parent_span_id"] == racine["span_id"]
    assert enfant["trace_id"] == racine["trace_id"]
    assert enfant["service_name"] == "service-test"
    assert enfant["start_time"] and enfant["end_time"]
    # Champs historiques conservés : rien de ce qui lisait le fichier ne casse.
    assert "duree_ms" in enfant and "attributs" in enfant and "erreur" in enfant


def test_jsonl_exporter_keeps_status_message(tmp_path):
    from opentelemetry.trace import Status, StatusCode

    output_path = tmp_path / "traces.jsonl"
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(JSONLSpanExporter(str(output_path))))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("appel_outil_test") as span:
        span.set_status(Status(StatusCode.ERROR, "echec simule"))

    trace_entry = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
    assert trace_entry["statut_message"] == "echec simule"


def test_resource_porte_le_service_name_et_l_environnement(monkeypatch):
    """Le service émetteur et l'environnement doivent être distinguables."""
    monkeypatch.setenv("APP_ENV", "preprod")

    attributs = tracing._build_resource("qualicheck-api-regles").attributes

    assert attributs["service.name"] == "qualicheck-api-regles"
    assert attributs["deployment.environment.name"] == "preprod"


def test_resource_environnement_par_defaut(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)

    assert tracing._build_resource("x").attributes["deployment.environment.name"] == "dev"


def test_get_tracer_ne_leve_jamais_sur_config_invalide(monkeypatch):
    """Une observabilité mal configurée ne doit pas tuer l'endpoint métier.

    `get_tracer()` est appelé depuis le chemin de requête : s'il levait, la
    question de l'utilisateur partirait en 503 à cause du traçage.
    """
    monkeypatch.setattr(tracing, "_provider", None)
    monkeypatch.setenv("OTEL_EXPORTER", "otlp")
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_BASE_URL", raising=False)

    tracer = tracing.get_tracer()

    # Tracer dégradé (provider par défaut) : on peut ouvrir un span sans erreur.
    with tracer.start_as_current_span("test"):
        pass
