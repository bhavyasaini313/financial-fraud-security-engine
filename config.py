import os

# Existing Configurations
RISK_WINDOW_HOURS = 48
SPIKE_THRESHOLD_PERCENTAGE = 500.0
LEDGER_FILE_PATH = "database/audit_ledger.json"

# New Enterprise Security Configurations
# In production, this would be loaded securely via environment variables
HMAC_SECRET_KEY = b"InstitutionalBankingSecretSigningKey2026"
SIEM_LOG_PATH = "database/siem_alerts.cef"