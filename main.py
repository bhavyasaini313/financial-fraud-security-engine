
import argparse
import logging
import json
import hmac
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from engine.crypto_vault import CryptographicLedger
from engine.analytics import ComplianceAnalyzer
from config import LEDGER_FILE_PATH, HMAC_SECRET_KEY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(name)s) %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("SystemCore")

def generate_signed_synthetic_data():
    """Generates synthetic data simulating secure API signed streaming payloads."""
    start_date = datetime(2026, 7, 1)
    accounts = ["ACC_9941", "ACC_2381", "ACC_0047"]
    rows = []
    for acc in accounts:
        for day in range(5):
            current_date = start_date + timedelta(days=day)
            rows.append({"timestamp": current_date.strftime("%Y-%m-%d 10:00:00"), "account_id": acc, "volume": int(np.random.randint(150, 450))})
    
    rows.append({"timestamp": "2026-07-06 14:22:00", "account_id": "ACC_9941", "volume": 2800})
    rows.append({"timestamp": "2026-07-06 14:45:00", "account_id": "ACC_2381", "volume": 3500})
    
    news_feed = pd.DataFrame([{"announcement_time": "2026-07-07 09:00:00", "ticker": "ALGN", "event": "Cross-Border Acquisition Strategy Finalization"}])
    market_df = pd.DataFrame(rows)
    
    # Generate cryptographic signature for transmission package integrity validation
    serialized_payload = market_df.to_json(orient="records")
    payload_signature = hmac.new(HMAC_SECRET_KEY, serialized_payload.encode(), hashlib.sha256).hexdigest()
    
    return market_df, news_feed, serialized_payload, payload_signature

def run_pipeline(vault, analyzer):
    logger.info("Ingesting secure data streaming pipeline...")
    market_feed, news_feed, raw_json, signature = generate_signed_synthetic_data()
    
    # 1. HMAC Payload Inspection Pass
    if not vault.verify_api_payload_signature(raw_json, signature):
        logger.error("HMAC Authentication Failed! Payload dropped due to mid-transit injection risk.")
        vault.export_to_siem("API_INTEGRITY_FAIL", "NETWORK_INGRESS", "Payload dropped: Cryptographic signature mismatch.", severity=9)
        return
    
    logger.info("✅ HMAC signature verified successfully. Processing analytics passes...")
    analyzer.process_market_activity(market_feed, news_feed)
    
    is_secure, audit_msg = vault.verify_ledger_integrity()
    logger.info(f"Audit Status Check: {audit_msg}")

def simulate_breach(vault):
    print("\n" + "="*80 + "\n[LAUNCHING SIMULATED STORAGE INTERACTION BREACH]\n" + "="*80)
    try:
        with open(LEDGER_FILE_PATH, "r") as f:
            raw_data = json.load(f)
        raw_data[0]["data"]["metrics"]["observed_volume"] = 10
        with open(LEDGER_FILE_PATH, "w") as f:
            json.dump(raw_data, f, indent=4)
        logger.warning("Database manipulation occurred. File state structural markers changed maliciously.")
        vault.export_to_siem("FILE_BREACH_SIMULATION", "ATTACK_VECTOR", "Database layer manipulated directly.", severity=8)
    except Exception as e:
        logger.error(f"Simulation block modification failed: {e}")
    print("="*80 + "\n")

def enforce_sweep(vault):
    logger.info("Executing comprehensive cryptographic health audit check...")
    is_secure, audit_msg = vault.verify_ledger_integrity()
    
    if not is_secure:
        logger.critical(f"INTEGRITY EXPLOIT FLAG RAISED: {audit_msg}")
        print("\n" + "🩺"*40 + "\n[AUTOMATED SELF-HEALING REGISTRY ROLLBACK ENFORCED]\n" + "🩺"*40)
        vault.trigger_self_healing()
        logger.info("Memory backup rollback complete. Storage layer completely synchronized.")
        
        # Post verification
        is_secure, audit_msg = vault.verify_ledger_integrity()
        if is_secure:
            logger.info(f"POST-HEALING RESYNC CONFIRMED: {audit_msg}")
    else:
        logger.info("✅ Core ledger system healthy. Integrity signatures perfectly verified.")

def main():
    parser = argparse.ArgumentParser(description="Enterprise Compliance & Autonomous Cyber Security Engine Controls")
    parser.add_argument("--scan", action="store_true", help="Ingest streaming market feeds and map anomalies.")
    parser.add_argument("--simulate-attack", action="store_true", help="Simulate a database manipulation hack vector.")
    parser.add_argument("--verify", action="store_true", help="Trigger a zero-trust cryptographic ledger validation sweep.")
    args = parser.parse_args()

    vault = CryptographicLedger()
    analyzer = ComplianceAnalyzer(vault)

    # If no flags passed, output manual usage parameters
    if not (args.scan or args.simulate_attack or args.verify):
        parser.print_help()
        return

    if args.scan:
        run_pipeline(vault, analyzer)
    if args.simulate_attack:
        simulate_breach(vault)
    if args.verify:
        enforce_sweep(vault)

if __name__ == "__main__":
    main()