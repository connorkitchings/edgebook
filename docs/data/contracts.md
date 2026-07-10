# Data Contracts

This document outlines the data contracts for various data assets within the project. Data contracts define the schema, quality expectations, and ownership of data.

## Table of Contents

- [Data Asset: [Asset Name]](#data-asset-asset-name)
  - [Schema](#schema)
  - [Quality Expectations](#quality-expectations)
  - [Ownership](#ownership)

## Data Asset: [Asset Name]

### Description
[Brief description of the data asset]

### Schema

```json
{
  "type": "object",
  "properties": {
    "field1": {
      "type": "string",
      "description": "Description of field1"
    },
    "field2": {
      "type": "integer",
      "minimum": 0
    }
  },
  "required": ["field1"]
}
```

### Quality Expectations

- **Freshness:** [e.g., updated daily, near real-time]
- **Completeness:** [e.g., 99% of records should have field1 populated]
- **Accuracy:** [e.g., field2 should be within +/- 5% of the true value]
- **Uniqueness:** [e.g., field1 should be unique]

### Ownership

- **Owner:** [Team or individual responsible for the data asset]
- **Contact:** [Email or communication channel]
