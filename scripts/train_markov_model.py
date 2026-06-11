"""Train a Markov chain model for message generation"""
import json
import pickle
from pathlib import Path
from collections import defaultdict
import random


def build_markov_chain(messages, order=1):
    """
    Build a Markov chain from messages

    Args:
        messages: List of message strings
        order: Order of the Markov chain (1 = bigram, 2 = trigram)

    Returns:
        Dictionary mapping words to possible next words
    """
    chain = defaultdict(list)

    for message in messages:
        # Tokenize
        words = ['<START>'] + message.split() + ['<END>']

        # Build chain
        for i in range(len(words) - order):
            if order == 1:
                current = words[i]
                next_word = words[i + 1]
            else:
                current = tuple(words[i:i + order])
                next_word = words[i + order]

            chain[current].append(next_word)

    return dict(chain)


def train_markov_models(training_data_file, output_file):
    """Train Markov models for each personality/risk combination"""

    print("="*60)
    print("TRAINING MARKOV CHAIN MODELS")
    print("="*60)
    print()

    # Load training data
    print(f"Loading training data from {training_data_file}...")
    with open(training_data_file, 'r') as f:
        training_data = json.load(f)

    print(f"Loaded {len(training_data)} training examples")

    # Group messages by personality and risk level
    grouped_messages = defaultdict(list)

    for example in training_data:
        personality = example['personality']
        risk = example['risk_level']
        message = example['message']

        key = f"{personality}_{risk}"
        grouped_messages[key].append(message)

    print(f"\nFound {len(grouped_messages)} personality/risk combinations:")
    for key, messages in grouped_messages.items():
        print(f"  {key}: {len(messages)} messages")

    # Train a Markov chain for each combination
    print("\nTraining Markov chains...")
    models = {}

    for key, messages in grouped_messages.items():
        print(f"  Training {key}...")
        chain = build_markov_chain(messages, order=1)
        models[key] = chain
        print(f"    ✓ Chain built with {len(chain)} states")

    # Save models
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving models to {output_path}...")
    with open(output_path, 'wb') as f:
        pickle.dump(models, f)

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Models saved to: {output_path}")
    print(f"Total models: {len(models)}")

    # Show sample generation
    print("\n" + "="*60)
    print("SAMPLE GENERATIONS")
    print("="*60)

    for key, chain in list(models.items())[:3]:  # Show first 3
        print(f"\n{key}:")
        for i in range(3):
            words = []
            current = '<START>'

            for _ in range(20):  # Max 20 words
                if current not in chain or not chain[current]:
                    break

                next_word = random.choice(chain[current])
                if next_word == '<END>':
                    break

                words.append(next_word)
                current = next_word

            message = ' '.join(words)
            print(f"  {i+1}. {message}")


def main():
    training_data_file = "app/ml_models/training_data/neural_training_data.json"
    output_file = "app/ml_models/markov_model.pkl"

    train_markov_models(training_data_file, output_file)


if __name__ == "__main__":
    main()
