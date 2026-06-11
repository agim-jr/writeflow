"""Train a neural sequence-to-sequence model for message generation"""
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
import pickle
from tqdm import tqdm
import random

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)
random.seed(42)


class MessageDataset(Dataset):
    """Dataset for training the neural model"""

    def __init__(self, data_file, max_length=200):
        # Load data
        with open(data_file) as f:
            self.data = json.load(f)

        self.max_length = max_length

        # Build vocabulary from all messages
        all_text = ''.join([ex['message'] for ex in self.data])

        # Also include special characters that might appear
        special_chars = '<>[]'
        all_text += special_chars

        self.chars = sorted(list(set(all_text)))
        self.vocab_size = len(self.chars)

        # Character mappings
        self.char_to_idx = {ch: i for i, ch in enumerate(self.chars)}
        self.idx_to_char = {i: ch for i, ch in enumerate(self.chars)}

        # Add special tokens for padding/start/end
        self.pad_token = '<PAD>'
        self.start_token = '<START>'
        self.end_token = '<END>'

        self.char_to_idx[self.pad_token] = self.vocab_size
        self.char_to_idx[self.start_token] = self.vocab_size + 1
        self.char_to_idx[self.end_token] = self.vocab_size + 2
        self.idx_to_char[self.vocab_size] = self.pad_token
        self.idx_to_char[self.vocab_size + 1] = self.start_token
        self.idx_to_char[self.vocab_size + 2] = self.end_token
        self.vocab_size += 3

        print(f"Vocabulary size: {self.vocab_size}")
        print(f"Characters: {''.join(self.chars[:50])}...")

        # Encode personality types
        personalities = list(set(ex['personality'] for ex in self.data))
        self.personality_to_idx = {p: i for i, p in enumerate(personalities)}
        self.n_personalities = len(personalities)

        # Encode risk levels
        risks = ['low', 'medium', 'high']
        self.risk_to_idx = {r: i for i, r in enumerate(risks)}
        self.n_risks = len(risks)

        print(f"Personalities: {list(self.personality_to_idx.keys())}")
        print(f"Risk levels: {risks}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        example = self.data[idx]

        # Encode context (personality, risk, streak, days)
        personality_idx = self.personality_to_idx[example['personality']]
        risk_idx = self.risk_to_idx[example['risk_level']]
        streak = example['current_streak']
        days = example['days_since_last_write']

        # Normalize numerical features
        streak_norm = min(streak / 365.0, 1.0)  # Normalize to [0, 1]
        days_norm = min(days / 7.0, 1.0)  # Normalize to [0, 1]

        context = torch.tensor([
            personality_idx / self.n_personalities,
            risk_idx / self.n_risks,
            streak_norm,
            days_norm
        ], dtype=torch.float32)

        # Encode message
        message = example['message']

        # Add START and END tokens
        message_with_tokens = self.start_token + message + self.end_token

        # Convert to indices, skip unknown characters
        char_indices = []
        for ch in message_with_tokens:
            if ch in self.char_to_idx:
                char_indices.append(self.char_to_idx[ch])

        # Ensure we have at least some content
        if len(char_indices) < 3:  # Less than START + END + 1 char
            char_indices = [
                self.char_to_idx[self.start_token],
                self.char_to_idx[' '],  # Space as fallback
                self.char_to_idx[self.end_token]
            ]

        # Pad to max_length
        if len(char_indices) < self.max_length:
            char_indices += [self.char_to_idx[self.pad_token]] * (self.max_length - len(char_indices))
        else:
            char_indices = char_indices[:self.max_length]

        # Input is all but last character, target is all but first
        input_seq = torch.tensor(char_indices[:-1], dtype=torch.long)
        target_seq = torch.tensor(char_indices[1:], dtype=torch.long)

        return context, input_seq, target_seq, len(message_with_tokens) - 1


class MessageGenerator(nn.Module):
    """Neural network for generating messages"""

    def __init__(self, vocab_size, context_size=4, embed_size=128,
                 hidden_size=256, num_layers=2, dropout=0.3):
        super().__init__()

        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Context encoder (MLP)
        self.context_encoder = nn.Sequential(
            nn.Linear(context_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, hidden_size),
            nn.ReLU()
        )

        # Character embedding
        self.embedding = nn.Embedding(vocab_size, embed_size)

        # LSTM for sequence generation
        self.lstm = nn.LSTM(
            embed_size + hidden_size,  # Concat char embed + context
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Output layer
        self.fc_out = nn.Linear(hidden_size, vocab_size)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(self, context, input_seq):
        """
        Args:
            context: (batch, context_size)
            input_seq: (batch, seq_len)
        Returns:
            output: (batch, seq_len, vocab_size)
        """
        batch_size = input_seq.size(0)
        seq_len = input_seq.size(1)

        # Encode context
        context_encoded = self.context_encoder(context)  # (batch, hidden_size)

        # Expand context to match sequence length
        context_expanded = context_encoded.unsqueeze(1).expand(-1, seq_len, -1)  # (batch, seq_len, hidden_size)

        # Embed input sequence
        embedded = self.embedding(input_seq)  # (batch, seq_len, embed_size)
        embedded = self.dropout(embedded)

        # Concatenate context with embeddings
        lstm_input = torch.cat([embedded, context_expanded], dim=2)  # (batch, seq_len, embed_size + hidden_size)

        # Pass through LSTM
        lstm_out, _ = self.lstm(lstm_input)  # (batch, seq_len, hidden_size)

        # Generate output
        output = self.fc_out(lstm_out)  # (batch, seq_len, vocab_size)

        return output

    def generate(self, context, char_to_idx, idx_to_char, start_token='<START>',
                 end_token='<END>', pad_token='<PAD>', max_length=200,
                 temperature=0.8, top_k=10):
        """Generate a message given context with top-k sampling"""
        self.eval()

        with torch.no_grad():
            current_char = torch.tensor([[char_to_idx[start_token]]], dtype=torch.long)
            generated = []

            start_idx = char_to_idx[start_token]
            end_idx = char_to_idx[end_token]
            pad_idx = char_to_idx[pad_token]

            context_encoded = self.context_encoder(context.unsqueeze(0))
            h = torch.zeros(self.num_layers, 1, self.hidden_size)
            c = torch.zeros(self.num_layers, 1, self.hidden_size)

            for step in range(max_length):
                embedded = self.embedding(current_char)
                lstm_input = torch.cat([embedded, context_encoded.unsqueeze(1)], dim=2)
                lstm_out, (h, c) = self.lstm(lstm_input, (h, c))
                logits = self.fc_out(lstm_out.squeeze(1))

                # Apply temperature
                logits = logits / temperature

                # Mask special tokens
                logits[0, start_idx] = -float('inf')
                logits[0, pad_idx] = -float('inf')

                # Top-k sampling
                if top_k > 0:
                    top_k_logits, top_k_indices = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits_filtered = torch.full_like(logits, -float('inf'))
                    logits_filtered.scatter_(1, top_k_indices, top_k_logits)
                    logits = logits_filtered

                probs = torch.softmax(logits, dim=1)
                next_char_idx = torch.multinomial(probs, 1).item()

                if next_char_idx == end_idx:
                    break

                if next_char_idx in idx_to_char and next_char_idx not in [start_idx, end_idx, pad_idx]:
                    char = idx_to_char[next_char_idx]
                    generated.append(char)

                current_char = torch.tensor([[next_char_idx]], dtype=torch.long)

            result = ''.join(generated)
            result = result.replace('<START>', '').replace('<END>', '').replace('<PAD>', '').strip()
            return result


def train_model(data_file, output_dir, epochs=50, batch_size=128, learning_rate=0.001):
    """Train the neural model"""

    print("="*60)
    print("TRAINING NEURAL MESSAGE GENERATOR")
    print("="*60)

    # Create dataset
    print("\nLoading dataset...")
    dataset = MessageDataset(data_file, max_length=200)

    # Split into train/val
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

    print(f"Training examples: {train_size}")
    print(f"Validation examples: {val_size}")

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    # Create model
    print("\nInitializing model...")
    model = MessageGenerator(
        vocab_size=dataset.vocab_size,
        context_size=4,
        embed_size=128,
        hidden_size=256,
        num_layers=2,
        dropout=0.3
    )

    # Count parameters
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {n_params:,}")

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(ignore_index=dataset.char_to_idx[dataset.pad_token])
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5)

    # Training loop
    best_val_loss = float('inf')

    print("\n" + "="*60)
    print("TRAINING")
    print("="*60)

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0

        for context, input_seq, target_seq, lengths in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            optimizer.zero_grad()

            # Forward pass
            output = model(context, input_seq)

            # Compute loss
            loss = criterion(output.view(-1, dataset.vocab_size), target_seq.view(-1))

            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0

        with torch.no_grad():
            for context, input_seq, target_seq, lengths in val_loader:
                output = model(context, input_seq)
                loss = criterion(output.view(-1, dataset.vocab_size), target_seq.view(-1))
                val_loss += loss.item()

        val_loss /= len(val_loader)

        # Update learning rate
        scheduler.step(val_loss)

        print(f"\nEpoch {epoch+1}/{epochs}")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss:   {val_loss:.4f}")
        print(f"  LR: {optimizer.param_groups[0]['lr']:.6f}")

        # Generate sample
        if (epoch + 1) % 5 == 0:
            print("\n  Sample generations:")

            # Sample contexts
            test_contexts = [
                {'personality': 'direct_challenging', 'risk': 'high', 'streak': 10, 'days': 6.5},
                {'personality': 'gentle_encouraging', 'risk': 'medium', 'streak': 30, 'days': 3},
                {'personality': 'analytical_factual', 'risk': 'low', 'streak': 7, 'days': 0},
            ]

            for ctx in test_contexts:
                # Encode context
                personality_idx = dataset.personality_to_idx[ctx['personality']]
                risk_idx = dataset.risk_to_idx[ctx['risk']]
                streak_norm = min(ctx['streak'] / 365.0, 1.0)
                days_norm = min(ctx['days'] / 7.0, 1.0)

                context_tensor = torch.tensor([
                    personality_idx / dataset.n_personalities,
                    risk_idx / dataset.n_risks,
                    streak_norm,
                    days_norm
                ], dtype=torch.float32)

                # Generate
                message = model.generate(
                    context_tensor,
                    dataset.char_to_idx,
                    dataset.idx_to_char,
                    start_token=dataset.start_token,
                    end_token=dataset.end_token,
                    pad_token=dataset.pad_token,
                    max_length=200,
                    temperature=0.8
                )

                print(f"    [{ctx['personality'][:10]}, {ctx['risk']}, {ctx['streak']}d, {ctx['days']}d]")
                print(f"    \"{message}\"")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss

            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save model
            torch.save(model.state_dict(), output_dir / "neural_model.pt")

            # Save vocab
            vocab_data = {
                'char_to_idx': dataset.char_to_idx,
                'idx_to_char': dataset.idx_to_char,
                'personality_to_idx': dataset.personality_to_idx,
                'risk_to_idx': dataset.risk_to_idx,
                'vocab_size': dataset.vocab_size,
                'n_personalities': dataset.n_personalities,
                'n_risks': dataset.n_risks,
                'pad_token': dataset.pad_token,
                'start_token': dataset.start_token,
                'end_token': dataset.end_token,
            }

            with open(output_dir / "vocab.pkl", 'wb') as f:
                pickle.dump(vocab_data, f)

            print(f"  ✓ Saved model (val_loss: {val_loss:.4f})")

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Model saved to: {output_dir}")


def main():
    data_file = "app/ml_models/training_data/neural_training_data.json"
    output_dir = "app/ml_models/neural"

    train_model(
        data_file=data_file,
        output_dir=output_dir,
        epochs=50,
        batch_size=128,
        learning_rate=0.001
    )


if __name__ == "__main__":
    main()
