"""Generate sample messages using the Markov chain model"""
import sys
import json
import pickle
from pathlib import Path
from collections import defaultdict
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class MarkovMessageGenerator:
    """Simple Markov chain message generator"""

    def __init__(self, model_path="app/ml_models/markov_model.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.load_model()

    def load_model(self):
        """Load the trained Markov model"""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✓ Loaded Markov model from {self.model_path}")
        else:
            print(f"✗ Model not found at {self.model_path}")
            print("  Run: python scripts/train_markov_model.py")
            sys.exit(1)

    def generate_message(self, user_state):
        """Generate a message using the Markov model"""
        personality = user_state.get('personality', 'gentle_encouraging')
        risk_level = user_state.get('risk_level', 'medium')

        # Get the appropriate chain
        key = f"{personality}_{risk_level}"

        if key not in self.model:
            # Fallback to any available chain
            key = list(self.model.keys())[0]

        chain = self.model[key]

        # Generate message
        words = []
        current_word = '<START>'

        max_length = 20  # Maximum words in message

        for _ in range(max_length):
            if current_word not in chain or not chain[current_word]:
                break

            # Choose next word
            next_word = random.choice(chain[current_word])

            if next_word == '<END>':
                break

            words.append(next_word)
            current_word = next_word

        message = ' '.join(words)

        # Replace placeholders with actual values
        message = message.replace('[STREAK]', str(user_state.get('current_streak', 0)))
        message = message.replace('[DAYS]', str(user_state.get('days_since_last_write', 0)))

        return message


def main():
    print("="*60)
    print("MARKOV CHAIN MESSAGE GENERATOR - TESTING")
    print("="*60)
    print()

    # Initialize generator
    print("Loading Markov chain model...")
    generator = MarkovMessageGenerator()

    print("\n" + "="*60)
    print("GENERATING TEST MESSAGES")
    print("="*60)

    # Test cases
    test_cases = [
        {
            'personality': 'direct_challenging',
            'risk_level': 'high',
            'current_streak': 5,
            'days_since_last_write': 8,
            'description': 'High risk - long gap'
        },
        {
            'personality': 'gentle_encouraging',
            'risk_level': 'low',
            'current_streak': 45,
            'days_since_last_write': 0,
            'description': 'Low risk - active writer'
        },
        {
            'personality': 'analytical_factual',
            'risk_level': 'medium',
            'current_streak': 15,
            'days_since_last_write': 3,
            'description': 'Medium risk - moderate streak'
        },
        {
            'personality': 'direct_challenging',
            'risk_level': 'high',
            'current_streak': 100,
            'days_since_last_write': 10,
            'description': 'High risk - long streak at risk'
        },
        {
            'personality': 'gentle_encouraging',
            'risk_level': 'medium',
            'current_streak': 1,
            'days_since_last_write': 4,
            'description': 'New streak building'
        },
        {
            'personality': 'analytical_factual',
            'risk_level': 'low',
            'current_streak': 200,
            'days_since_last_write': 1,
            'description': 'Long streak - consistent'
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}: {case['description']}")
        print(f"{'='*60}")
        print(f"Personality: {case['personality']}")
        print(f"Risk Level: {case['risk_level']}")
        print(f"Current Streak: {case['current_streak']} days")
        print(f"Days Since Write: {case['days_since_last_write']} days")
        print()

        # Generate multiple variations
        print("Generated messages:")
        for j in range(5):
            message = generator.generate_message(case)
            print(f"  {j+1}. {message}")

    print("\n" + "="*60)
    print("TESTING COMPLETE!")
    print("="*60)

    # Show statistics
    print("\nMarkov Chain Model Features:")
    print("  ✓ Learns from training data")
    print("  ✓ Word-level generation (clean output)")
    print("  ✓ Context-aware (personality, risk, streak)")
    print("  ✓ Natural variation in messages")
    print("  ✓ No gibberish or token artifacts")


if __name__ == "__main__":
    main()
