import logging
from datetime import timedelta
import pandas as pd
from config import RISK_WINDOW_HOURS, SPIKE_THRESHOLD_PERCENTAGE

logger = logging.getLogger("IntelligenceEngine")

class ComplianceAnalyzer:
    def __init__(self, ledger_instance):
        self.ledger = ledger_instance

    def process_market_activity(self, trades_df: pd.DataFrame, news_df: pd.DataFrame):
        """Ingests temporal data and looks for sudden high-volume anomalies inside risk timelines."""
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        news_df['announcement_time'] = pd.to_datetime(news_df['announcement_time'])
        
        announcement_dt = news_df.iloc[0]['announcement_time']
        risk_window_start = announcement_dt - timedelta(hours=RISK_WINDOW_HOURS)
        
        # Segment data arrays using vectorized pandas mapping
        historical_baseline_pool = trades_df[trades_df['timestamp'] < risk_window_start]
        critical_window_pool = trades_df[(trades_df['timestamp'] >= risk_window_start) & (trades_df['timestamp'] <= announcement_dt)]
        
        # Build mathematical averages dictionary profiles per account
        baseline_profiles = historical_baseline_pool.groupby('account_id')['volume'].mean().to_dict()
        
        for _, transaction in critical_window_pool.iterrows():
            account = transaction['account_id']
            observed_vol = transaction['volume']
            historical_avg = baseline_profiles.get(account, 0)
            
            if historical_avg > 0:
                deviation_ratio = (observed_vol / historical_avg) * 100
                if deviation_ratio >= SPIKE_THRESHOLD_PERCENTAGE:
                    alert_payload = {
                        "event_type": "HIGH_RISK_TIMING_ANOMALY",
                        "account_id": account,
                        "metrics": {
                            "observed_volume": int(observed_vol),
                            "historical_average": round(historical_avg, 2),
                            "deviation_percentage": f"{round(deviation_ratio, 2)}%"
                        },
                        "context": {
                            "trade_timestamp": transaction['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                            "market_trigger_event": news_df.iloc[0]['event']
                        }
                    }
                    logger.warning(f"🚨 Anomalous trading spike caught for client asset: {account}")
                    self.ledger.commit_alert(alert_payload)