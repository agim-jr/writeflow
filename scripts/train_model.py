"""Script to train the message generation model."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_models.message_generation.trainer import ModelTrainer
from app.ml_models.message_generation.config import ModelConfig


def main():
    """Train the message generation model."""

    print("=" * 60)
    print("MESSAGE GENERATION MODEL TRAINING")
    print("=" * 60)

    # Initialize config
    config = ModelConfig()

    # Check if training data exists
    if not os.path.exists(config.TRAINING_DATA_PATH):
        print(f"\n✗ Training data not found at: {config.TRAINING_DATA_PATH}")
        print("  Run 'python scripts/generate_seed_data.py' first")
        return

    # Count training examples
    with open(config.TRAINING_DATA_PATH, 'r') as f:
        num_examples = sum(1 for _ in f)

    print(f"\nTraining Configuration:")
    print(f"  Data path: {config.TRAINING_DATA_PATH}")
    print(f"  Total examples: {num_examples}")
    print(f"  Batch size: {config.BATCH_SIZE}")
    print(f"  Learning rate: {config.LEARNING_RATE}")
    print(f"  Epochs: {config.NUM_EPOCHS}")
    print(f"  Device: {config.DEVICE}")
    print(f"\nModel Architecture:")
    print(f"  Embedding dim: {config.EMBEDDING_DIM}")
    print(f"  Hidden dim: {config.HIDDEN_DIM}")
    print(f"  Num layers: {config.NUM_LAYERS}")
    print(f"  Dropout: {config.DROPOUT}")

    # Ask for confirmation
    response = input("\nStart training? (y/n): ")
    if response.lower() != 'y':
        print("Training cancelled.")
        return

    # Initialize trainer
    trainer = ModelTrainer(config)

    try:
        # Train model
        model, vocab = trainer.train(
            data_path=config.TRAINING_DATA_PATH,
            num_epochs=config.NUM_EPOCHS
        )

        print("\n" + "=" * 60)
        print("TRAINING SUMMARY")
        print("=" * 60)
        print(f"✓ Model saved to: {config.MODEL_SAVE_PATH}")
        print(f"✓ Vocabulary saved to: {config.VOCAB_SAVE_PATH}")
        print(f"✓ Final train loss: {trainer.train_losses[-1]:.4f}")
        print(f"✓ Final val loss: {trainer.val_losses[-1]:.4f}")
        print(f"✓ Vocabulary size: {len(vocab)}")

        # Test generation with a few examples
        print("\n" + "=" * 60)
        print("SAMPLE GENERATIONS")
        print("=" * 60)

        test_cases = [
            {
                'personality': 'direct_challenging',
                'risk': 'high',
                'streak': 5,
                'days': 3,
                'desc': 'Direct, high risk, streak at risk'
            },
            {
                'personality': 'gentle_encouraging',
                'risk': 'low',
                'streak': 10,
                'days': 0,
                'desc': 'Gentle, low risk, consistent writer'
            },
            {
                'personality': 'humorous_playful',
                'risk': 'medium',
                'streak': 0,
                'days': 7,
                'desc': 'Humorous, medium risk, new user'
            }
        ]

        model.eval()
        for i, test in enumerate(test_cases, 1):
            message = model.generate_message(
                personality=test['personality'],
                risk_level=test['risk'],
                streak=test['streak'],
                days_since_last_write=test['days'],
                vocab=vocab,
                temperature=config.TEMPERATURE,
                top_k=config.TOP_K
            )
            print(f"\n{i}. {test['desc']}")
            print(f"   Personality: {test['personality']}")
            print(f"   Risk: {test['risk']}, Streak: {test['streak']}, Days: {test['days']}")
            print(f"   → \"{message}\"")

        print("\n" + "=" * 60)
        print("✓ Training complete! You can now:")
        print("  1. Test the model: python scripts/test_model.py")
        print("  2. Evaluate performance: python scripts/evaluate_model.py")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user.")
        print("Model state has been saved at the last checkpoint.")
    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
