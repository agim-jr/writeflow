"""Script to evaluate model performance on test data."""
import sys
import os
import json
import torch
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_models.message_generation.inference import MessageInference
from app.ml_models.message_generation.config import ModelConfig


def load_test_data(data_path, split=0.1):
    """Load test data from training file."""
    all_data = []
    with open(data_path, 'r') as f:
        for line in f:
            all_data.append(json.loads(line))

    # Use last 10% as test set
    test_size = int(len(all_data) * split)
    test_data = all_data[-test_size:]

    return test_data


def calculate_metrics(inference, test_data):
    """Calculate evaluation metrics."""

    metrics = {
        'total': len(test_data),
        'by_personality': defaultdict(lambda: {'count': 0, 'avg_length': 0}),
        'by_risk': defaultdict(lambda: {'count': 0, 'avg_length': 0}),
        'overall_avg_length': 0,
        'generation_success': 0
    }

    total_length = 0

    print("\nEvaluating model on test data...")
    print(f"Total test examples: {len(test_data)}")

    for i, example in enumerate(test_data, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(test_data)}")

        try:
            # Generate message
            message = inference.generate(
                personality=example['personality'],
                risk_level=example['risk_level'],
                user_context=example['context']
            )

            # Track success
            if message and len(message) > 0:
                metrics['generation_success'] += 1
                msg_length = len(message)
                total_length += msg_length

                # Track by personality
                p = example['personality']
                metrics['by_personality'][p]['count'] += 1
                metrics['by_personality'][p]['avg_length'] += msg_length

                # Track by risk
                r = example['risk_level']
                metrics['by_risk'][r]['count'] += 1
                metrics['by_risk'][r]['avg_length'] += msg_length

        except Exception as e:
            print(f"  Error on example {i}: {e}")

    # Calculate averages
    if metrics['generation_success'] > 0:
        metrics['overall_avg_length'] = total_length / metrics['generation_success']

        for p in metrics['by_personality']:
            count = metrics['by_personality'][p]['count']
            if count > 0:
                metrics['by_personality'][p]['avg_length'] /= count

        for r in metrics['by_risk']:
            count = metrics['by_risk'][r]['count']
            if count > 0:
                metrics['by_risk'][r]['avg_length'] /= count

    metrics['success_rate'] = metrics['generation_success'] / metrics['total'] * 100

    return metrics


def display_metrics(metrics):
    """Display evaluation metrics."""

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    print(f"\nOverall Performance:")
    print(f"  Total examples: {metrics['total']}")
    print(f"  Successful generations: {metrics['generation_success']}")
    print(f"  Success rate: {metrics['success_rate']:.1f}%")
    print(f"  Average message length: {metrics['overall_avg_length']:.1f} characters")

    print(f"\nPerformance by Personality:")
    for personality, stats in sorted(metrics['by_personality'].items()):
        print(f"  {personality}:")
        print(f"    Count: {stats['count']}")
        print(f"    Avg length: {stats['avg_length']:.1f} chars")

    print(f"\nPerformance by Risk Level:")
    for risk, stats in sorted(metrics['by_risk'].items()):
        print(f"  {risk}:")
        print(f"    Count: {stats['count']}")
        print(f"    Avg length: {stats['avg_length']:.1f} chars")


def generate_comparison_samples(inference, test_data, num_samples=5):
    """Generate comparison samples between expected and generated."""

    print("\n" + "=" * 60)
    print("SAMPLE COMPARISONS (Expected vs Generated)")
    print("=" * 60)

    import random
    samples = random.sample(test_data, min(num_samples, len(test_data)))

    for i, example in enumerate(samples, 1):
        print(f"\n{'─' * 60}")
        print(f"Sample {i}")
        print(f"{'─' * 60}")
        print(f"Personality: {example['personality']}")
        print(f"Risk Level: {example['risk_level']}")
        print(f"Streak: {example['context']['current_streak']}")
        print(f"Days Since: {example['context']['days_since_last_write']}")
        print(f"\nExpected message:")
        print(f"  \"{example['message']}\"")

        # Generate 2 variations
        print(f"\nGenerated messages:")
        for j in range(2):
            try:
                message = inference.generate(
                    personality=example['personality'],
                    risk_level=example['risk_level'],
                    user_context=example['context']
                )
                print(f"  {j+1}. \"{message}\"")
            except Exception as e:
                print(f"  {j+1}. Error: {e}")


def main():
    """Run model evaluation."""

    config = ModelConfig()

    # Check if model exists
    if not os.path.exists(config.MODEL_SAVE_PATH):
        print(f"\n✗ Model not found at: {config.MODEL_SAVE_PATH}")
        print("  Train the model first: python scripts/train_model.py")
        return

    # Check if training data exists
    if not os.path.exists(config.TRAINING_DATA_PATH):
        print(f"\n✗ Training data not found at: {config.TRAINING_DATA_PATH}")
        return

    print("=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    # Load model
    print("\nLoading model...")
    inference = MessageInference()
    if not inference.load():
        print("✗ Failed to load model")
        return
    print("✓ Model loaded successfully")

    # Load test data
    print("\nLoading test data...")
    test_data = load_test_data(config.TRAINING_DATA_PATH)
    print(f"✓ Loaded {len(test_data)} test examples")

    # Calculate metrics
    metrics = calculate_metrics(inference, test_data)

    # Display results
    display_metrics(metrics)

    # Generate comparison samples
    generate_comparison_samples(inference, test_data)

    print("\n" + "=" * 60)
    print("✓ Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
