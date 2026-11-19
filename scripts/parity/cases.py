"""
Parity cases (plan Phase 2.3): inputs and variants. Seeds are fixed and every matrix is stored in the fixtures.

A case is `(name, project_name, policies, decision_makers, variants)`; `decision_makers` is a list of
`(name, n x n label matrix)`. A variant is a dict with `name`, `method` (the requested method), and optional
`weights`, `median_choice` and `tie_pick` (`first`, `last` or `middle`).
"""

import random
from typing import Dict, List, Tuple

from constants import COHERENCE_RATINGS, DIAGONAL_VALUE

Matrix = List[List[str]]
Case = Tuple[str, str, List[str], List[Tuple[str, Matrix]], List[Dict]]

NEGATIVE_LABELS = ["Constraining", "Counteracting", "Cancelling"]
POLICY_NAMES = [
    "Urban Mobility Plan",
    "Renewable Energy Act",
    "Water Resources Strategy",
    "Agricultural Subsidy Reform",
    "Green bonds worth $5bn and $3bn",
    "Biodiversity Action Plan",
    "Circular Economy Package",
    "Coastal Protection Programme",
]


def policies(count: int) -> List[str]:
    """Return `count` distinct policy names (the named list first, then `Policy {k}`)."""
    names = list(POLICY_NAMES[:count])
    return names + [f"Policy {k}" for k in range(len(names) + 1, count + 1)]


def random_matrix(rng: random.Random, n: int, labels: List[str]) -> Matrix:
    """Return an `n x n` label matrix with a Neutral diagonal and seeded random off-diagonal labels."""
    return [[DIAGONAL_VALUE if i == j else rng.choice(labels) for j in range(n)] for i in range(n)]


def constant_matrix(n: int, label: str) -> Matrix:
    """Return an `n x n` matrix holding one label off the diagonal."""
    return [[DIAGONAL_VALUE if i == j else label for j in range(n)] for i in range(n)]


def seeded(seed: int, n: int, dm_count: int, labels: List[str] = COHERENCE_RATINGS) -> List[Tuple[str, Matrix]]:
    """Return `dm_count` seeded random decision-maker matrices."""
    rng = random.Random(seed)
    return [(f"DM {k + 1}", random_matrix(rng, n, labels)) for k in range(dm_count)]


def all_methods(dm_count: int) -> List[Dict]:
    """Average, median, majority (first tied label) and equal-weight weighted."""
    return [
        {"name": "average", "method": "average"},
        {"name": "median", "method": "median"},
        {"name": "majority_first", "method": "majority", "tie_pick": "first"},
        {"name": "weighted", "method": "weighted", "weights": [1 / dm_count] * dm_count},
    ]


def weighted_d_weights() -> List[float]:
    """Eight seeded weights rounded to 3 dp; the last is 1 minus the sum of the others."""
    rng = random.Random(8)
    raw = [rng.uniform(0.5, 1.5) for _ in range(8)]
    total = sum(raw)
    first = [round(value / total, 3) for value in raw[:7]]
    return first + [1 - sum(first)]


def paths_case() -> List[Tuple[str, Matrix]]:
    """Seven policies, four DMs; equal-length shortest paths with averaged scores of 1, 1.5, 0.75 and 2."""
    cells = {
        (0, 1): ["Reinforcing", "Reinforcing", "Enabling", "Enabling"],  # 1.5 -> d = 2/3
        (1, 3): ["Reinforcing", "Reinforcing", "Enabling", "Enabling"],  # 1.5 -> d = 2/3
        (0, 3): ["Enabling", "Enabling", "Enabling", "Neutral"],  # 0.75 -> d = 4/3
        (0, 2): ["Enabling"] * 4,  # 1 -> d = 1
        (2, 6): ["Constraining"] * 4,  # -1 -> d = 1
        (0, 4): ["Reinforcing"] * 4,  # 2 -> d = 0.5
        (4, 5): ["Reinforcing"] * 4,  # 2 -> d = 0.5
        (5, 6): ["Enabling"] * 4,  # 1 -> d = 1
        (3, 6): ["Counteracting"] * 4,  # -2 -> d = 0.5
        (6, 0): ["Cancelling"] * 4,  # -3
        (6, 1): ["Enabling"] * 4,
    }
    matrices = []
    for k in range(4):
        matrix = constant_matrix(7, "Neutral")
        for (i, j), labels in cells.items():
            matrix[i][j] = labels[k]
        matrices.append((f"DM {k + 1}", matrix))
    return matrices


def small_cases() -> List[Case]:
    """The hand-built cases with fewer than five policies."""
    neutral = [(f"DM {k + 1}", constant_matrix(3, "Neutral")) for k in range(3)]
    onelink = constant_matrix(3, "Neutral")
    onelink[0][1] = "Reinforcing"
    negzero = [constant_matrix(3, "Neutral") for _ in range(3)]
    negzero[0][0][1] = "Constraining"
    for matrix in negzero:
        matrix[1][2] = "Enabling"
        matrix[2][0] = "Reinforcing"
    two = seeded(23, 2, 3)
    return [
        ("neutral3x3", "Parity neutral3x3", policies(3), neutral, all_methods(3)),
        (
            "onelink3x1",
            "Parity onelink3x1",
            policies(3),
            [("DM 1", onelink)],
            [{"name": "average", "method": "average"}],
        ),
        ("two2x3", "Parity two2x3", policies(2), two, all_methods(3)),
        (
            "two2x1",
            "Parity two2x1",
            policies(2),
            [("DM 1", [["Neutral", "Indivisible"], ["Neutral", "Neutral"]])],
            [{"name": "average", "method": "average"}],
        ),
        (
            "weighted_negzero",
            "Parity weighted_negzero",
            policies(3),
            [(f"DM {k + 1}", matrix) for k, matrix in enumerate(negzero)],
            [{"name": "weighted", "method": "weighted", "weights": [0.004, 0.498, 0.498]}],
        ),
    ]


def build_cases(example: Tuple[List[str], List[Tuple[str, Matrix]]]) -> List[Case]:
    """Return every analysis case; `example` is the legacy import of the bundled workbook."""
    identical = seeded(55, 5, 1) * 3
    identical = [(f"DM {k + 1}", matrix) for k, (_, matrix) in enumerate(identical)]
    return [
        (
            "example",
            "WEF Nexus Example",
            example[0],
            example[1],
            [{"name": "average", "method": "average"}, {"name": "requested_median", "method": "median"}],
        ),
        (
            "r5x3",
            "Parity r5x3",
            policies(5),
            seeded(51, 5, 3),
            [
                {"name": "average", "method": "average"},
                {"name": "median", "method": "median"},
                {"name": "majority_first", "method": "majority", "tie_pick": "first"},
                {"name": "majority_last", "method": "majority", "tie_pick": "last"},
                {"name": "majority_middle", "method": "majority", "tie_pick": "middle"},
                {"name": "weighted_a", "method": "weighted", "weights": [0.2, 0.3, 0.5]},
            ],
        ),
        (
            "r6x4",
            "Parity r6x4",
            policies(6),
            seeded(64, 6, 4),
            [
                {"name": "median_lower", "method": "median", "median_choice": "lower"},
                {"name": "median_upper", "method": "median", "median_choice": "upper"},
                {"name": "majority_first", "method": "majority", "tie_pick": "first"},
                {"name": "majority_last", "method": "majority", "tie_pick": "last"},
                {"name": "average", "method": "average"},
                {"name": "weighted_equal", "method": "weighted", "weights": [0.25] * 4},
                {"name": "weighted_b", "method": "weighted", "weights": [0.1, 0.2, 0.3, 0.4]},
            ],
        ),
        (
            "r8x8",
            "Parity r8x8",
            policies(8),
            seeded(88, 8, 8),
            [
                {"name": "average", "method": "average"},
                {"name": "weighted_c", "method": "weighted", "weights": [0.125] * 8},
                {"name": "weighted_d", "method": "weighted", "weights": weighted_d_weights()},
            ],
        ),
        *small_cases(),
        ("negative6x3", "Parity negative6x3", policies(6), seeded(63, 6, 3, NEGATIVE_LABELS), all_methods(3)),
        ("paths7x4", "Parity paths7x4", policies(7), paths_case(), [{"name": "average", "method": "average"}]),
        ("identical5x3", "Parity identical5x3", policies(5), identical, all_methods(3)),
        (
            "r30x5",
            "Parity r30x5",
            policies(30),
            seeded(305, 30, 5),
            [
                {"name": "average", "method": "average"},
                {"name": "majority_first", "method": "majority", "tie_pick": "first"},
            ],
        ),
    ]
