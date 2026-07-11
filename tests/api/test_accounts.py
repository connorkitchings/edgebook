"""API coverage for fictional account and statement endpoints."""


def test_create_get_and_transact_on_account(client):
    """A manual tester can open, fund, withdraw from, and inspect an account."""
    created = client.post(
        "/accounts", json={"owner_name": "Dana Allocator", "starting_bankroll": "12.34"}
    )
    assert created.status_code == 201
    account = created.json()
    assert account["starting_bankroll"] == "12.34"
    assert account["current_balance"] == "12.34"

    deposit = client.post(
        f"/accounts/{account['id']}/transactions",
        json={"type": "DEPOSIT", "amount": "3.00", "description": "Practice credit"},
    )
    assert deposit.status_code == 201
    assert deposit.json()["transaction"]["amount"] == "3.00"
    assert deposit.json()["current_balance"] == "15.34"

    withdrawal = client.post(
        f"/accounts/{account['id']}/transactions",
        json={"type": "WITHDRAWAL", "amount": "1.00"},
    )
    assert withdrawal.status_code == 201
    assert withdrawal.json()["transaction"]["amount"] == "-1.00"

    retrieved = client.get(f"/accounts/{account['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["current_balance"] == "14.34"

    statement = client.get(f"/accounts/{account['id']}/transactions?limit=2&offset=0")
    assert statement.status_code == 200
    assert statement.json()["total"] == 3
    assert len(statement.json()["items"]) == 2
    assert statement.json()["items"][0]["journal_entry_id"]


def test_account_endpoint_errors_and_amount_validation(client):
    """Account APIs return documented validation and conflict codes."""
    assert client.post("/accounts", json={"owner_name": "  "}).status_code == 422
    assert (
        client.post(
            "/accounts", json={"owner_name": "Dana", "starting_bankroll": "1.001"}
        ).status_code
        == 422
    )
    assert client.get("/accounts/missing").status_code == 404

    account = client.post("/accounts", json={"owner_name": "Dana"}).json()
    assert (
        client.post(
            f"/accounts/{account['id']}/transactions",
            json={"type": "WAGER_STAKE", "amount": "1.00"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/accounts/{account['id']}/transactions",
            json={"type": "DEPOSIT", "amount": "0.001"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/accounts/{account['id']}/transactions",
            json={"type": "WITHDRAWAL", "amount": "1.00"},
        ).status_code
        == 409
    )


def test_reconciliation_verifies_materialized_balance_matches_postings(client):
    """Reconciliation confirms the stored balance equals the sum of postings."""
    account = client.post(
        "/accounts", json={"owner_name": "Reconciler", "starting_bankroll": "50.00"}
    ).json()
    client.post(
        f"/accounts/{account['id']}/transactions",
        json={"type": "DEPOSIT", "amount": "10.00"},
    )
    result = client.post(f"/accounts/{account['id']}/reconcile").json()
    assert result["is_balanced"] is True
    assert result["materialized_balance"] == "60.00"
    assert result["computed_balance"] == "60.00"
    assert result["discrepancy"] == "0.00"

    assert client.post("/accounts/missing/reconcile").status_code == 404
