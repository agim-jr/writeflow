"""Script to test the trained model interactively."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_models.message_generation.inference import MessageInference
from app.ml_models.message_generation.config import ModelConfig


def display_menu():
    """Display the test menu."""
    print("\n" + "=" * 60)
    print("MESSAGE GENERATION MODEL - INTERACTIVE TESTING")
    print("=" * 60)
    print("\nPersonality Types:")
    config = ModelConfig()
    for i, p in enumerate(config.PERSONALITY_TYPES, 1):
        print(f"  {i}. {p}")

    print("\nRisk Levels:")
    for i, r in enumerate(config.RISK_LEVELS, 1):
        print(f"  {i}. {r}")

    print("\n" + "=" * 60)


def get_user_input():
    """Get test parameters from user."""
    config = ModelConfig()

    print("\nEnter test parameters:")

    # Get personality
    print("\nPersonality types:")
    for i, p in enumerate(config.PERSONALITY_TYPES, 1):
        print(f"  {i}. {p}")

    while True:
        try:
            p_idx = int(input("Select personality (1-7): ")) - 1
            if 0 <= p_idx < len(config.PERSONALITY_TYPES):
                personality = config.PERSONALITY_TYPES[p_idx]
                break
        except (ValueError, IndexError):
            pass
        print("Invalid selection. Try again.")

    # Get risk level
    print("\nRisk levels:")
    for i, r in enumerate(config.RISK_LEVELS, 1):
        print(f"  {i}. {r}")

    while True:
        try:
            r_idx = int(input("Select risk level (1-3): ")) - 1
            if 0 <= r_idx < len(config.RISK_LEVELS):
                risk_level = config.RISK_LEVELS[r_idx]
                break
        except (ValueError, IndexError):
            pass
        print("Invalid selection. Try again.")

    # Get streak
    while True:
        try:
            streak = int(input("Enter current streak (0-365): "))
            if 0 <= streak <= 365:
                break
        except ValueError:
            pass
        print("Invalid streak. Try again.")

    # Get days since last write
    while True:
        try:
            days_since = int(input("Enter days since last write (0-30): "))
            if 0 <= days_since <= 30:
                break
        except ValueError:
            pass
        print("Invalid days. Try again.")

    # Get temperature (optional)
    temp_input = input("\nSampling temperature (default 0.8, press Enter to skip): ").strip()
    temperature = float(temp_input) if temp_input else None

    # Get top_k (optional)
    topk_input = input("Top-k sampling (default 50, press Enter to skip): ").strip()
    top_k = int(topk_input) if topk_input else None

    return {
        'personality': personality,
        'risk_level': risk_level,
        'user_context': {
            'current_streak': streak,
            'days_since_last_write': days_since
        },
        'temperature': temperature,
        'top_k': top_k
    }


def run_predefined_tests(inference):
    """Run a set of predefined test cases."""
    print("\n" + "=" * 60)
    print("RUNNING PREDEFINED TEST CASES")
    print("=" * 60)

    test_cases = [
        {
            'name': 'New user, gentle approach',
            'personality': 'gentle_encouraging',
            'risk_level': 'low',
            'user_context': {'current_streak': 0, 'days_since_last_write': 0}
        },
        {
            'name': 'Consistent writer, keep motivated',
            'personality': 'aspirational_visionary',
            'risk_level': 'low',
            'user_context': {'current_streak': 30, 'days_since_last_write': 0}
        },
        {
            'name': 'Streak at risk, urgent push',
            'personality': 'direct_challenging',
            'risk_level': 'high',
            'user_context': {'current_streak': 10, 'days_since_last_write': 2}
        },
        {
            'name': 'Long absence, empathetic return',
            'personality': 'empathetic_understanding',
            'risk_level': 'medium',
            'user_context': {'current_streak': 0, 'days_since_last_write': 14}
        },
        {
            'name': 'Regular writer, playful reminder',
            'personality': 'humorous_playful',
            'risk_level': 'low',
            'user_context': {'current_streak': 7, 'days_since_last_write': 1}
        },
        {
            'name': 'Data-driven user, show stats',
            'personality': 'analytical_factual',
            'risk_level': 'medium',
            'user_context': {'current_streak': 15, 'days_since_last_write': 1}
        },
        {
            'name': 'Reflective user, deeper meaning',
            'personality': 'philosophical_reflective',
            'risk_level': 'low',
            'user_context': {'current_streak': 5, 'days_since_last_write': 0}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'─' * 60}")
        print(f"Personality: {test['personality']}")
        print(f"Risk Level: {test['risk_level']}")
        print(f"Streak: {test['user_context']['current_streak']}")
        print(f"Days Since Last Write: {test['user_context']['days_since_last_write']}")

        # Generate 3 variations
        print("\nGenerated Messages:")
        for j in range(3):
            message = inference.generate(
                personality=test['personality'],
                risk_level=test['risk_level'],
                user_context=test['user_context']
            )
            print(f"  {j+1}. \"{message}\"")


def main():
    """Run the interactive test interface."""

    config = ModelConfig()

    # Check if model exists
    if not os.path.exists(config.MODEL_SAVE_PATH):
        print(f"\n✗ Model not found at: {config.MODEL_SAVE_PATH}")
        print("  Train the model first: python scripts/train_model.py")
        return

    # Load model
    print("\nLoading model...")
    inference = MessageInference()
    if not inference.load():
        print("✗ Failed to load model")
        return

    print("✓ Model loaded successfully\n")

    # Main menu
    while True:
        print("\n" + "=" * 60)
        print("TEST OPTIONS")
        print("=" * 60)
        print("1. Custom test (enter your own parameters)")
        print("2. Run predefined test cases")
        print("3. Batch generation test")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == '1':
            # Custom test
            params = get_user_input()
            print("\n" + "─" * 60)
            print("Generating message...")
            print("─" * 60)

            message = inference.generate(**params)

            print(f"\nGenerated Message:")
            print(f"  \"{message}\"")
            print(f"\nParameters used:")
            print(f"  Personality: {params['personality']}")
            print(f"  Risk Level: {params['risk_level']}")
            print(f"  Streak: {params['user_context']['current_streak']}")
            print(f"  Days Since: {params['user_context']['days_since_last_write']}")
            if params['temperature']:
                print(f"  Temperature: {params['temperature']}")
            if params['top_k']:
                print(f"  Top-k: {params['top_k']}")

        elif choice == '2':
            # Predefined tests
            run_predefined_tests(inference)

        elif choice == '3':
            # Batch generation
            print("\n" + "=" * 60)
            print("BATCH GENERATION TEST")
            print("=" * 60)

            num = input("How many messages to generate? (1-20): ").strip()
            try:
                num = int(num)
                if 1 <= num <= 20:
                    import random
                    contexts = []
                    for _ in range(num):
                        contexts.append({
                            'personality': random.choice(config.PERSONALITY_TYPES),
                            'risk_level': random.choice(config.RISK_LEVELS),
                            'user_context': {
                                'current_streak': random.randint(0, 100),
                                'days_since_last_write': random.randint(0, 7)
                            }
                        })

                    print(f"\nGenerating {num} messages...")
                    messages = inference.batch_generate(contexts)

                    print("\nResults:")
                    for i, (ctx, msg) in enumerate(zip(contexts, messages), 1):
                        print(f"\n{i}. {ctx['personality']} / {ctx['risk_level']}")
                        print(f"   Streak: {ctx['user_context']['current_streak']}, "
                              f"Days: {ctx['user_context']['days_since_last_write']}")
                        print(f"   → \"{msg}\"")
                else:
                    print("Invalid number")
            except ValueError:
                print("Invalid input")

        elif choice == '4':
            print("\nExiting test interface. Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
