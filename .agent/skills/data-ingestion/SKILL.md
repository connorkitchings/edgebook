---
name: data-ingestion
description: "Implement data ingestion adapters for external data sources with idempotent upserts."
metadata:
  trigger-keywords: "ingestion, data source, adapter, etl, pipeline"
  trigger-patterns: "^ingest, ^data source, ^adapter, ^etl"
---

# Data Ingestion Skill

Implement ingestion adapters for external data sources with proper error handling, retries, and idempotent operations.

---

## When to Use

- Adding new external data source
- Creating ETL pipeline for data warehouse
- Implementing data sync from APIs
- Building data collection automation

**Do NOT use when:**
- One-time manual data import (use notebooks)
- Real-time streaming (use different architecture)
- Data is already in database (use migration skill)

---

## Inputs

### Required
- Data source: API, file, database, etc.
- Schema: What fields to extract
- Destination: Where to store (database, files)
- Rate limits: API restrictions

### Optional
- Authentication: API keys, OAuth tokens
- Incremental logic: How to detect new data
- Validation rules: Data quality checks

---

## Steps

### Step 1: Design Adapter

**What to do:**
Design the adapter interface and data flow.

**Design Pattern:**
```python
# src/ingestion/adapters/base.py
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any

class DataAdapter(ABC):
    """Base class for data ingestion adapters."""
    
    @abstractmethod
    def fetch(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """Fetch data from source. Yields records."""
        pass
    
    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> bool:
        """Validate record before storage."""
        pass
    
    @abstractmethod
    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record to target schema."""
        pass
```

**Validation:**
- [ ] Interface defined
- [ ] Error handling strategy clear
- [ ] Rate limiting approach identified

### Step 2: Implement Fetch Logic

**What to do:**
Implement data fetching with retries and backoff.

**Code Pattern:**
```python
# src/ingestion/adapters/example_api.py
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

class ExampleAPIAdapter(DataAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.example.com/v1"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=lambda e: isinstance(e, (requests.Timeout, requests.ConnectionError))
    )
    def fetch(self, start_date: str = None, end_date: str = None):
        """Fetch data with pagination and retries."""
        page = 1
        while True:
            response = requests.get(
                f"{self.base_url}/data",
                params={
                    "api_key": self.api_key,
                    "page": page,
                    "start_date": start_date,
                    "end_date": end_date
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            for record in data["results"]:
                yield record
            
            if not data["has_more"]:
                break
            page += 1
            
            # Rate limiting
            time.sleep(1)  # Respect API limits
```

**Validation:**
- [ ] Pagination handled
- [ ] Retries configured
- [ ] Rate limiting implemented
- [ ] Timeout set

### Step 3: Implement Transform

**What to do:**
Transform source data to target schema.

**Code Pattern:**
```python
def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
    """Transform API record to database schema."""
    return {
        "source_id": record["id"],
        "name": record["name"].strip().title(),
        "created_at": parse_datetime(record["created_at"]),
        "metadata": {
            "source": "example_api",
            "version": record.get("version", "1.0")
        }
    }
```

**Validation:**
- [ ] Type conversions handled
- [ ] Null values managed
- [ ] Date/time parsing robust
- [ ] Metadata preserved

### Step 4: Implement Persistence

**What to do:**
Implement idempotent upsert to database.

**Code Pattern:**
```python
# src/ingestion/persistence.py
from sqlalchemy.dialects.postgresql import insert

def upsert_records(session, model, records: list, conflict_columns: list):
    """Idempotent upsert - safe to re-run."""
    if not records:
        return 0
    
    stmt = insert(model).values(records)
    
    # Update on conflict (upsert)
    update_dict = {
        c.name: c for c in stmt.excluded if c.name not in conflict_columns
    }
    
    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_=update_dict
    )
    
    result = session.execute(stmt)
    return result.rowcount

# Usage
adapter = ExampleAPIAdapter(api_key="xxx")
records = []

for record in adapter.fetch(start_date="2026-01-01"):
    if adapter.validate(record):
        records.append(adapter.transform(record))
    
    # Batch insert
    if len(records) >= 1000:
        upsert_records(session, DataModel, records, ["source_id"])
        records = []

# Final batch
if records:
    upsert_records(session, DataModel, records, ["source_id"])
```

**Validation:**
- [ ] Upsert logic correct
- [ ] Batch processing implemented
- [ ] Conflict columns identified
- [ ] Transaction handling proper

### Step 5: Add Validation

**What to do:**
Implement data quality checks.

**Code Pattern:**
```python
def validate(self, record: Dict[str, Any]) -> bool:
    """Validate record before storage."""
    required_fields = ["id", "name", "created_at"]
    
    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False
    
    # Type validation
    if not isinstance(record["id"], (int, str)):
        logger.warning(f"Invalid id type: {type(record['id'])}")
        return False
    
    # Business rules
    if len(record.get("name", "")) < 1:
        logger.warning("Empty name")
        return False
    
    return True
```

**Validation:**
- [ ] Required fields checked
- [ ] Data types validated
- [ ] Business rules enforced
- [ ] Invalid records logged

### Step 6: Create CLI Script

**What to do:**
Create runnable ingestion script.

**Code Pattern:**
```python
# scripts/ingest_example.py
import typer
from datetime import datetime, timedelta
from src.ingestion.adapters.example_api import ExampleAPIAdapter
from src.ingestion.persistence import upsert_records
from src.database import SessionLocal

app = typer.Typer()

@app.command()
def ingest(
    start_date: str = None,
    end_date: str = None,
    full: bool = False
):
    """Ingest data from Example API."""
    if full:
        start_date = "2020-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    adapter = ExampleAPIAdapter(api_key=config.EXAMPLE_API_KEY)
    session = SessionLocal()
    
    try:
        total = 0
        records = []
        
        for record in adapter.fetch(start_date, end_date):
            if adapter.validate(record):
                records.append(adapter.transform(record))
            
            if len(records) >= 1000:
                count = upsert_records(session, DataModel, records, ["source_id"])
                total += count
                session.commit()
                records = []
                typer.echo(f"Ingested {total} records...")
        
        # Final batch
        if records:
            count = upsert_records(session, DataModel, records, ["source_id"])
            total += count
            session.commit()
        
        typer.echo(f"Complete! Total records: {total}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    app()
```

---

## Validation

### Success Criteria
- [ ] Adapter implements base interface
- [ ] Fetch includes retries and rate limiting
- [ ] Transform handles all data types
- [ ] Persistence is idempotent
- [ ] Validation catches bad data
- [ ] CLI script runnable

### Verification Commands
```bash
# Test ingestion
uv run python scripts/ingest_example.py --start-date 2026-01-01

# Run validation
uv run pytest tests/ingestion/test_example_adapter.py -v

# Check data quality
uv run python scripts/validate_data.py
```

---

## Rollback

### If Ingestion Goes Wrong

```bash
# Check what was ingested
psql -d mydb -c "SELECT COUNT(*) FROM data_model WHERE created_at > '2026-01-01'"

# Delete bad data (if needed)
psql -d mydb -c "DELETE FROM data_model WHERE source = 'example_api' AND created_at > '2026-01-01'"

# Or rollback transaction (if caught early)
# Ingestion should use transactions - rollback on error
```

---

## Common Mistakes

1. **No rate limiting**: Always respect API limits
2. **Missing retries**: Network errors will happen
3. **No idempotency**: Running twice creates duplicates
4. **No validation**: Bad data corrupts database
5. **No batching**: Inserting one record at a time is slow
6. **No logging**: Can't debug when things go wrong

---

## Related Skills

- **Database Migration**: For creating tables to store ingested data
- **API Endpoint**: If exposing ingested data via API
- **Test Writer**: For writing ingestion tests

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **Data Sources**: `docs/data/sources/`
- **Knowledge Base**: `docs/knowledge_base.md`

---

## Examples

### Example 1: API Ingestion

**Scenario:** Ingest daily weather data from external API.

**Pattern:**
- Daily incremental ingestion
- Upsert by date + location
- Validate temperature ranges
- Store raw JSON in metadata

### Example 2: File Ingestion

**Scenario:** Process uploaded CSV files.

**Pattern:**
- Watch directory for new files
- Parse CSV with validation
- Move processed files to archive
- Log processing statistics

---

**Remember: Always test with small batches first!**
