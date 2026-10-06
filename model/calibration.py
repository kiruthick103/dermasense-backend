"""
Model Calibration via Temperature Scaling.
Learns a single scalar temperature parameter on the validation set to optimize
probability calibration without affecting accuracy or ranking. Computes Expected
Calibration Error (ECE) and reliability bin diagrams.
"""

from typing import Dict, List, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


def compute_ece(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10
) -> Tuple[float, List[Dict[str, float]]]:
    """
    Computes Expected Calibration Error (ECE) and reliability table.

    Parameters:
      probs: Array of predicted probabilities for positive class (N,).
      labels: Ground-truth binary labels (N,) with values in {0, 1}.
      n_bins: Number of equal-width confidence bins in [0, 1].

    Returns:
      ece: Expected Calibration Error weighted by bin occupancy.
      reliability_table: List of dicts with bin statistics (confidence, accuracy, count).
    """
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n_total = len(labels)
    reliability_table = []

    if n_total == 0:
        return 0.0, []

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Samples within confidence bin
        if i == n_bins - 1:
            in_bin = (probs >= bin_lower) & (probs <= bin_upper)
        else:
            in_bin = (probs >= bin_lower) & (probs < bin_upper)

        bin_count = int(np.sum(in_bin))
        if bin_count > 0:
            bin_acc = float(np.mean(labels[in_bin]))
            bin_conf = float(np.mean(probs[in_bin]))
            bin_weight = bin_count / float(n_total)
            ece += bin_weight * abs(bin_acc - bin_conf)
            reliability_table.append({
                "bin_lower": round(bin_lower, 2),
                "bin_upper": round(bin_upper, 2),
                "count": bin_count,
                "confidence": round(bin_conf, 4),
                "accuracy": round(bin_acc, 4),
                "gap": round(abs(bin_acc - bin_conf), 4),
            })
        else:
            reliability_table.append({
                "bin_lower": round(bin_lower, 2),
                "bin_upper": round(bin_upper, 2),
                "count": 0,
                "confidence": 0.0,
                "accuracy": 0.0,
                "gap": 0.0,
            })

    return round(float(ece), 4), reliability_table


class TemperatureScaler(nn.Module):
    """
    A wrapper around model logits that divides logits by temperature T.
    T is learned on validation data via L-BFGS to minimize negative log likelihood.
    """
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        # Constrain temperature to be strictly positive
        temp = torch.clamp(self.temperature, min=0.01)
        return logits / temp

    def fit(self, val_logits: torch.Tensor, val_labels: torch.Tensor, max_iter: int = 50) -> float:
        """
        Learns temperature parameter on validation set.
        Never use the final test set for temperature fitting.
        """
        nll_criterion = nn.BCEWithLogitsLoss()
        optimizer = optim.LBFGS([self.temperature], lr=0.01, max_iter=max_iter)

        def eval_loss():
            optimizer.zero_grad()
            scaled_logits = self.forward(val_logits)
            loss = nll_criterion(scaled_logits.view(-1), val_labels.float().view(-1))
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        return float(self.temperature.item())
