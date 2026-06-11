# scripts\test_data_collector.py
"""Test the data collector"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml_models.message_generation.data_collector import MessageDataCollector

def test_collector():
    collector = MessageDataCollector()

    # Test saving an interaction
    example = collector.save_interaction(
        personality='direct_challenging',
        risk_level='medium',
        user_context={
            'current_streak': 15,
            'days_since_last': 1.8,
            'avg_word_count': 350,
            'total_entries': 50,
            'avg_sentiment': 0.4
        },
        message="Your streak is at risk. Write today.",
        response_type='wrote_within_60min',
        time_to_action=22.5
    )

    print("✓ Saved interaction:")
    print(f"  Personality: {example.personality}")
    print(f"  Risk: {example.risk_level}")
    print(f"  Effectiveness: {example.effectiveness}")
    print(f"  Message: {example.message}")

    # Get stats
    stats = collector.get_stats()
    print(f"\n✓ Training data stats:")
    print(f"  Total examples: {stats['total_examples']}")
    print(f"  Average effectiveness: {stats['avg_effectiveness']:.2f}")

if __name__ == '__main__':
    test_collector()
