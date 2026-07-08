import json
import os
import hmac
import hashlib
from datetime import datetime
from config import HMAC_SECRET_KEY, SIEM_LOG_PATH

class CryptographicLedger:
    def __init__(self):
        self.ledger_path = "database/audit_ledger.json"
        self._secure_memory_backup = []
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        self._load_initial_ledger()

    def _load_initial_ledger(self):
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._secure_memory_backup = json.loads(json.dumps(data))
            except:
                pass

    def verify_api_payload_signature(self, serialized_data, incoming_signature):
        """Verifies if incoming transaction data has been altered in transit (Anti-MitM)."""
        calculated_sig = hmac.new(HMAC_SECRET_KEY, serialized_data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated_sig, incoming_signature)

    def export_to_siem(self, event_type, account_id, message, severity=6):
        """Formats logs into Common Event Format (CEF) for SIEM systems like Splunk/QRadar."""
        timestamp = datetime.utcnow().strftime("%b %d %H:%M:%S")
        cef_msg = f"{timestamp} CEF:0|FinTechSecurity|FraudEngine|1.0|{event_type}|{message}|{severity}|src={account_id}\n"
        
        with open(SIEM_LOG_PATH, 'a') as f:
            f.write(cef_msg)

    def commit_alert(self, alert_payload):
        ledger_data = []
        if os.path.exists(self.ledger_path) and os.path.getsize(self.ledger_path) > 0:
            with open(self.ledger_path, 'r') as f:
                try:
                    ledger_data = json.load(f)
                except json.JSONDecodeError:
                    ledger_data = []

        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        if len(ledger_data) > 0:
            prev_hash = ledger_data[-1]["current_hash"]

        block_index = len(ledger_data) + 1
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        payload = {
            "index": block_index,
            "timestamp": timestamp,
            "prev_hash": prev_hash,
            "data": alert_payload
        }

        block_string = json.dumps(payload["data"], sort_keys=True) + prev_hash + timestamp + str(block_index)
        current_hash = hashlib.sha256(block_string.encode()).hexdigest()
        payload["current_hash"] = current_hash

        ledger_data.append(payload)

        with open(self.ledger_path, 'w') as f:
            json.dump(ledger_data, f, indent=4)
        
        self._secure_memory_backup = json.loads(json.dumps(ledger_data))
        
        # Log to SIEM ledger tracking
        self.export_to_siem("FRAUD_ALERT_GENERATED", alert_payload["account_id"], f"Cryptographic Block #{block_index} sealed.", severity=7)

    def verify_ledger_integrity(self):
        if not os.path.exists(self.ledger_path):
            return False, "Ledger file missing completely."

        with open(self.ledger_path, 'r') as f:
            try:
                ledger_data = json.load(f)
            except json.JSONDecodeError:
                return False, "Ledger parsing failed (Structural Corruption)."

        for i, block in enumerate(ledger_data):
            expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000" if i == 0 else ledger_data[i-1]["current_hash"]
            if block["prev_hash"] != expected_prev_hash:
                return False, f"Broken chain linkage detected at Block #{block['index']}"

            block_string = json.dumps(block["data"], sort_keys=True) + block["prev_hash"] + block["timestamp"] + str(block["index"])
            calculated_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if block["current_hash"] != calculated_hash:
                return False, f"Structural modification detected inside Block #{block['index']}!"

        return True, "Ledger verified. Cryptographic trail matches signature requirements perfectly."

    def trigger_self_healing(self):
        with open(self.ledger_path, 'w') as f:
            json.dump(self._secure_memory_backup, f, indent=4)
        self.export_to_siem("LEDGER_RECOVERY", "SYSTEM", "Self-healing triggered. Disk state restored from memory.", severity=10)