"""Test the trained neural model"""
import torch
import pickle
from pathlib import Path
import sys
sys.path.append('.')

from scripts.train_neural_model import MessageGenerator


def load_model(model_dir="app/ml_models/neural"):
    """Load the trained model and vocabulary"""
    model_dir = Path(model_dir)

    print(f"Loading from: {model_dir}")

    # Load vocabulary
    vocab_path = model_dir / "vocab.pkl"
    print(f"Loading vocabulary from {vocab_path}...")
    with open(vocab_path, 'rb') as f:
        vocab = pickle.load(f)

    print(f"Vocabulary loaded: {vocab['vocab_size']} characters")
    print(f"Personalities: {list(vocab['personality_to_idx'].keys())}")

    # Create model
    print("Creating model...")
    model = MessageGenerator(
        vocab_size=vocab['vocab_size'],
        context_size=4,
        embed_size=128,
        hidden_size=256,
        num_layers=2,
        dropout=0.3
    )

    # Load weights
    model_path = model_dir / "neural_model.pt"
    print(f"Loading weights from {model_path}...")
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()

    print("Model loaded successfully!\n")

    return model, vocab


def generate_message(model, vocab, personality, risk_level, streak, days_since_write, temperature=0.8, top_k=10):
    """Generate a message with given context"""

    try:
        # Encode context
        personality_idx = vocab['personality_to_idx'][personality]
        risk_idx = vocab['risk_to_idx'][risk_level]
        streak_norm = min(streak / 365.0, 1.0)
        days_norm = min(days_since_write / 7.0, 1.0)

        context = torch.tensor([
            personality_idx / vocab['n_personalities'],
            risk_idx / vocab['n_risks'],
            streak_norm,
            days_norm
        ], dtype=torch.float32)

        # Generate with top-k sampling
        message = model.generate(
            context,
            vocab['char_to_idx'],
            vocab['idx_to_char'],
            start_token=vocab['start_token'],
            end_token=vocab['end_token'],
            pad_token=vocab['pad_token'],
            max_length=200,
            temperature=temperature,
            top_k=top_k
        )

        return message if message else "[No message generated]"

    except Exception as e:
        return f"[Error: {str(e)}]"


def main():
    try:
        print("="*60)
        print("NEURAL MESSAGE GENERATOR - TESTING")
        print("="*60)
        print()

        print("Loading model...")
        model, vocab = load_model()

        print("="*60)
        print("GENERATING TEST MESSAGES")
        print("="*60)

        # Test cases
        test_cases = [
            {
                'personality': 'direct_challenging',
                'risk': 'high',
                'streak': 5,
                'days': 8,
                'description': 'High risk - long gap'
            },
            {
                'personality': 'gentle_encouraging',
                'risk': 'low',
                'streak': 45,
                'days': 0,
                'description': 'Low risk - active writer'
            },
            {
                'personality': 'analytical_factual',
                'risk': 'medium',
                'streak': 15,
                'days': 3,
                'description': 'Medium risk - moderate streak'
            },
            {
                'personality': 'direct_challenging',
                'risk': 'high',
                'streak': 100,
                'days': 10,
                'description': 'High risk - long streak at risk'
            },
            {
                'personality': 'gentle_encouraging',
                'risk': 'medium',
                'streak': 1,
                'days': 4,
                'description': 'New streak building'
            },
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {case['description']}")
            print(f"{'='*60}")
            print(f"Personality: {case['personality']}")
            print(f"Risk Level: {case['risk']}")
            print(f"Current Streak: {case['streak']} days")
            print(f"Days Since Write: {case['days']} days")
            print()

            # Generate 3 variations with different temperatures and top-k
            print("Generated messages (with top-k=10 sampling):")
            for temp in [0.5, 0.7, 0.9]:
                message = generate_message(
                    model, vocab,
                    case['personality'],
                    case['risk'],
                    case['streak'],
                    case['days'],
                    temperature=temp,
                    top_k=10
                )
                print(f"\n  Temperature {temp}:")
                print(f"  \"{message}\"")

            # Also try with more restrictive top-k
            print("\n  With top-k=5 (more focused):")
            message = generate_message(
                model, vocab,
                case['personality'],
                case['risk'],
                case['streak'],
                case['days'],
                temperature=0.7,
                top_k=5
            )
            print(f"  \"{message}\"")

        print("\n" + "="*60)
        print("TESTING COMPLETE!")
        print("="*60)

        # Show model info
        print("\nNOTE: If output quality is poor, consider:")
        print("  1. Retraining with more data")
        print("  2. Using the Markov chain model instead")
        print("  3. Adjusting temperature (lower = more conservative)")
        print("  4. Adjusting top-k (lower = more focused)")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
