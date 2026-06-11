import torch
import torch.nn as nn
from typing import Dict, List
from datetime import datetime


class BehavioralStateLSTM(nn.Module):
    def __init__(self, input_features=15, hidden_size=128, num_layers=2, output_classes=5):
        super(BehavioralStateLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_features,
            hidden_size,
            num_layers,
            batch_first=True,
            bidirectional=True
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,
            num_heads=4,
            batch_first=True
        )

        # Classification head
        self.fc = nn.Sequential(
            nn.Linear(hidden_size * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, output_classes),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        last_hidden = attn_out[:, -1, :]
        output = self.fc(last_hidden)
        return output


class StateDetector:
    def __init__(self, model_path: str = None):
        self.states = ['flow', 'blocked', 'procrastinating', 'struggling', 'rushing']
        self.model = BehavioralStateLSTM()

        if model_path:
            self.model.load_state_dict(torch.load(model_path))

        self.model.eval()

    def extract_features(self, typing_events: list) -> torch.Tensor:
        """Extract behavioral features from typing events."""
        features = []
        window_size = 60

        for i in range(0, len(typing_events), window_size):
            window = typing_events[i:i+window_size]

            if len(window) < 10:
                continue

            feature_vector = [
                self._typing_speed(window),
                self._pause_frequency(window),
                self._delete_rate(window),
                self._average_word_length(window),
                self._sentence_completion_rate(window),
                self._backspace_burst_rate(window),
                self._typing_rhythm_variance(window),
                self._keystroke_interval_mean(window),
                self._keystroke_interval_std(window),
                self._capital_letter_ratio(window),
                self._punctuation_density(window),
                self._cursor_movement_frequency(window),
                self._selection_events(window),
                self._time_of_day(window[0].get('timestamp', datetime.utcnow())),
                self._session_duration(window)
            ]

            features.append(feature_vector)

        return torch.tensor(features, dtype=torch.float32) if features else torch.zeros((1, 15))

    def predict_state(self, typing_events: list) -> dict:
        """Predict current psychological state."""
        if not typing_events:
            return {'state': 'unknown', 'confidence': 0}

        features = self.extract_features(typing_events)

        if features.shape[0] == 0:
            return {'state': 'unknown', 'confidence': 0}

        features = features.unsqueeze(0)

        with torch.no_grad():
            probabilities = self.model(features)[0]

        state_idx = torch.argmax(probabilities).item()
        confidence = probabilities[state_idx].item()

        return {
            'state': self.states[state_idx],
            'confidence': confidence,
            'probabilities': {
                state: prob.item()
                for state, prob in zip(self.states, probabilities)
            }
        }

    def _typing_speed(self, window):
        chars = sum(1 for e in window if e.get('type') == 'keypress')
        duration = 60  # seconds
        return (chars / 5) / (duration / 60) if duration > 0 else 0

    def _pause_frequency(self, window):
        return 0.1

    def _delete_rate(self, window):
        deletes = sum(1 for e in window if e.get('key') in ['Backspace', 'Delete'])
        return deletes / len(window) if window else 0

    def _average_word_length(self, window):
        return 5.0

    def _sentence_completion_rate(self, window):
        return 0.8

    def _backspace_burst_rate(self, window):
        return 0.1

    def _typing_rhythm_variance(self, window):
        return 0.2

    def _keystroke_interval_mean(self, window):
        return 0.15

    def _keystroke_interval_std(self, window):
        return 0.05

    def _capital_letter_ratio(self, window):
        return 0.1

    def _punctuation_density(self, window):
        return 0.05

    def _cursor_movement_frequency(self, window):
        return 0.02

    def _selection_events(self, window):
        return 0.01

    def _time_of_day(self, timestamp):
        if isinstance(timestamp, datetime):
            return timestamp.hour / 24.0
        return 0.5

    def _session_duration(self, window):
        return len(window) / 60.0
