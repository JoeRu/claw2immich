Show the **architecture summary** from the project overview.

## Steps

1. **Read** `ai-docs/overview.xml`.
2. **Display** a formatted summary of the project architecture:

## Output Format

```
Project Overview: {title}
=========================
Version: {version} | Last analyzed: {analyzed} | Last updated: {updated}

Architecture:
  {description}
  Patterns: {patterns list}

System Requirements:
  - {requirement 1}
  - {requirement 2}

External Dependencies:
  - {dependency 1}
  - {dependency 2}

Interfaces:
  Inbound:
    - {interface description}
  Outbound:
    - {interface description}

Environments:
  - {env name}: {details}

Security Concerns: {count}
  - [{risk level}] {threat} → {mitigation}

Completed Features: {count}
  - CF{id}: {title} (completeness: {level}, tests: {level})

Design Decisions:
  - [{date}] {decision}
```

3. If `overview.xml` doesn't exist, inform the user to run `/init` first.
