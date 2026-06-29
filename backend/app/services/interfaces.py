"""Abstract interfaces for future AI/ML detection engines (Level 2+).

These are Protocol definitions (structural sub-typing) only.
Do NOT implement these here — they are contracts for SecBERT, Autoencoder,
session-level anomaly detection, and meta-learner ensemble engines.
"""
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ClassificationResult:
    label: str
    confidence: float
    metadata: dict = field(default_factory=dict)


@dataclass
class AnomalyResult:
    is_anomaly: bool
    anomaly_score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class SessionRisk:
    risk_score: float
    signals: list[str] = field(default_factory=list)


@dataclass
class MetaDecision:
    decision: str  # 'allowed' | 'blocked'
    confidence: float
    contributing_engines: list[str] = field(default_factory=list)


@runtime_checkable
class AttackClassifier(Protocol):
    """SecBERT or similar transformer-based attack classifier.

    Implementations should load a fine-tuned model and expose
    synchronous or async inference.
    """

    async def classify(self, text: str) -> ClassificationResult:
        """Classify the given text and return a label with confidence."""
        ...

    async def is_ready(self) -> bool:
        """Return True when the model is loaded and ready to serve."""
        ...


@runtime_checkable
class AnomalyDetector(Protocol):
    """Autoencoder-based anomaly detection engine.

    Expects a feature dict representing the current request and returns an
    anomaly score normalised to [0, 1].
    """

    async def detect(self, features: dict) -> AnomalyResult:
        """Detect anomalies in the given feature vector."""
        ...

    async def is_ready(self) -> bool:
        """Return True when the model is loaded and calibrated."""
        ...


@runtime_checkable
class SessionAnalyzer(Protocol):
    """Session-level behavioural analysis engine.

    Tracks per-session signals (request rate, path entropy, user-agent
    consistency, etc.) and produces a risk score.
    """

    async def analyze_session(
        self, session_id: str, request: dict
    ) -> SessionRisk:
        """Analyse the current request in the context of its session."""
        ...


@runtime_checkable
class MetaLearner(Protocol):
    """Ensemble decision engine combining all detection signals.

    Aggregates outputs from the rule engine, classifier, and anomaly
    detector to produce a final allow/block decision.
    """

    async def decide(
        self,
        rule_result: dict,
        classifier_result: dict | None,
        anomaly_result: dict | None,
    ) -> MetaDecision:
        """Produce a final decision given all available signals."""
        ...
