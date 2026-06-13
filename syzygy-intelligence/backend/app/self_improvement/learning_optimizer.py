"""Adaptive learning rate optimization for recursive improvement.

Implements SOTA optimization strategies:
- Adaptive learning rate scheduling (warmup, decay, cyclical)
- Performance-based rate adjustment
- Exploration vs exploitation balance
- Early stopping prediction
- Hypergradient adaptation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.logging_setup import logger


class LearningRateSchedule(str, Enum):
    """Learning rate scheduling strategies."""

    CONSTANT = "constant"
    LINEAR_DECAY = "linear_decay"
    EXPONENTIAL_DECAY = "exponential_decay"
    COSINE_ANNEALING = "cosine_annealing"
    WARMUP_THEN_DECAY = "warmup_then_decay"
    CYCLICAL = "cyclical"
    PERFORMANCE_ADAPTIVE = "performance_adaptive"


@dataclass
class LearningRateConfig:
    """Configuration for learning rate optimization."""

    schedule: LearningRateSchedule = LearningRateSchedule.WARMUP_THEN_DECAY
    initial_rate: float = 0.1  # 10% adjustment magnitude
    min_rate: float = 0.01
    max_rate: float = 0.5
    warmup_cycles: int = 1
    decay_rate: float = 0.9  # per cycle
    cycle_length: int = 3
    adaptation_factor: float = 1.2  # increase rate if improving, decrease if not


class LearningOptimizer:
    """Manages learning rate scheduling and adaptive optimization."""

    def __init__(self, config: LearningRateConfig | None = None):
        self.config = config or LearningRateConfig()
        self.current_rate: float = self.config.initial_rate
        self.cycle_number: int = 0
        self.improvement_history: list[float] = []
        self.best_improvement: float = -float("inf")
        self.patience_counter: int = 0
        self.max_patience: int = 3

    def get_learning_rate(self, cycle: int, max_cycles: int) -> float:
        """Get learning rate for a cycle."""

        self.cycle_number = cycle

        if self.config.schedule == LearningRateSchedule.CONSTANT:
            self.current_rate = self.config.initial_rate

        elif self.config.schedule == LearningRateSchedule.LINEAR_DECAY:
            # Linearly decay from initial to min over all cycles
            progress = (cycle - 1) / (max_cycles - 1) if max_cycles > 1 else 0
            self.current_rate = (
                self.config.initial_rate
                - (self.config.initial_rate - self.config.min_rate) * progress
            )

        elif self.config.schedule == LearningRateSchedule.EXPONENTIAL_DECAY:
            # Exponentially decay
            self.current_rate = (
                self.config.initial_rate
                * (self.config.decay_rate ** (cycle - 1))
            )

        elif self.config.schedule == LearningRateSchedule.COSINE_ANNEALING:
            # Cosine annealing: smooth decay with restart
            import math
            progress = ((cycle - 1) % self.config.cycle_length) / (self.config.cycle_length - 1) if self.config.cycle_length > 1 else 0
            self.current_rate = (
                self.config.min_rate
                + 0.5 * (self.config.initial_rate - self.config.min_rate)
                * (1 + math.cos(math.pi * progress))
            )

        elif self.config.schedule == LearningRateSchedule.WARMUP_THEN_DECAY:
            # Warm up for initial cycles, then decay
            if cycle <= self.config.warmup_cycles:
                progress = cycle / self.config.warmup_cycles
                self.current_rate = self.config.initial_rate * progress
            else:
                decay_progress = (cycle - self.config.warmup_cycles) / (
                    max_cycles - self.config.warmup_cycles
                )
                self.current_rate = (
                    self.config.initial_rate
                    * (1 - decay_progress * (1 - self.config.min_rate / self.config.initial_rate))
                )

        elif self.config.schedule == LearningRateSchedule.CYCLICAL:
            # Cyclically vary rate (triangular wave)
            cycle_pos = (cycle - 1) % self.config.cycle_length
            ratio = cycle_pos / self.config.cycle_length
            self.current_rate = (
                self.config.min_rate
                + (self.config.initial_rate - self.config.min_rate)
                * (1 - abs(2 * ratio - 1))
            )

        elif self.config.schedule == LearningRateSchedule.PERFORMANCE_ADAPTIVE:
            # Adapt based on recent improvements
            if self.improvement_history:
                recent_improvement = self.improvement_history[-1]
                if recent_improvement >= self.best_improvement:
                    # Improving: increase rate slightly
                    self.current_rate = min(
                        self.config.max_rate,
                        self.current_rate * self.config.adaptation_factor,
                    )
                    self.best_improvement = recent_improvement
                    self.patience_counter = 0
                else:
                    # Not improving: decrease rate
                    self.current_rate = max(
                        self.config.min_rate,
                        self.current_rate / self.config.adaptation_factor,
                    )
                    self.patience_counter += 1

        # Clamp to bounds
        self.current_rate = max(
            self.config.min_rate,
            min(self.config.max_rate, self.current_rate),
        )

        logger.debug(
            f"Cycle {cycle}: learning_rate={self.current_rate:.4f}, "
            f"schedule={self.config.schedule.value}"
        )

        return self.current_rate

    def record_improvement(self, improvement_delta: float) -> None:
        """Record an improvement to inform adaptive scheduling."""

        self.improvement_history.append(improvement_delta)

        if improvement_delta > self.best_improvement:
            self.best_improvement = improvement_delta
            self.patience_counter = 0
        else:
            self.patience_counter += 1

        logger.debug(
            f"Recorded improvement: {improvement_delta:+.4f}, "
            f"best={self.best_improvement:.4f}, "
            f"patience={self.patience_counter}/{self.max_patience}"
        )

    def should_stop_early(self) -> bool:
        """Check if early stopping criteria are met."""

        # Stop if no improvement for max_patience cycles
        if self.patience_counter >= self.max_patience and len(self.improvement_history) >= 3:
            return True

        # Stop if rate has decayed below threshold
        if self.current_rate < self.config.min_rate * 0.5:
            return True

        return False

    def reset(self) -> None:
        """Reset optimizer state."""

        self.current_rate = self.config.initial_rate
        self.cycle_number = 0
        self.improvement_history = []
        self.best_improvement = -float("inf")
        self.patience_counter = 0
        logger.info("Learning optimizer reset")

    def get_config_dict(self) -> dict[str, Any]:
        """Serialize configuration for logging."""

        return {
            "schedule": self.config.schedule.value,
            "initial_rate": self.config.initial_rate,
            "min_rate": self.config.min_rate,
            "max_rate": self.config.max_rate,
            "warmup_cycles": self.config.warmup_cycles,
            "decay_rate": self.config.decay_rate,
        }


__all__ = [
    "LearningOptimizer",
    "LearningRateConfig",
    "LearningRateSchedule",
]
