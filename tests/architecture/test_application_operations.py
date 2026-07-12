"""Regression coverage for application-level orchestration delegates."""

from edgebook.application import operations


def test_review_claim_orchestration_delegates_to_wagering_workflow(monkeypatch):
    """The legacy scheduler command reaches reviews through application only."""
    db = object()
    expected = [object()]

    def fake_claim(received_db, *, limit: int):
        assert received_db is db
        assert limit == 7
        return expected

    monkeypatch.setattr(operations, "claim_pending_review_tasks", fake_claim)
    assert operations.claim_pending_reviews(db, limit=7) == expected
