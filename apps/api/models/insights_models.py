"""`InsightsData`: only what the legacy Results Insights tab displays, plus the per-policy fields of the story."""

from typing import List, Optional

from pydantic import BaseModel, Field


class InsightsRow(BaseModel):
    """One policy's enriched row (`results_insights_tab.py:617-641`) with its role (`:503-509`)."""

    code: str
    policy: str
    oi: int
    ii: int
    woi: float
    wii: float
    net: float
    prominence: float
    entropy: float
    entropy_category: str
    betweenness: float
    closeness: float
    role: str = Field(description="`driver`, `dependent` or `balanced` (net cut-off ±0.05)")


class GraphStats(BaseModel):
    """Relation counts and the strongest links (`results_insights_tab.py:312-352`)."""

    positive_edges: int
    negative_edges: int
    zero_edges: int
    density: float
    polarity: float
    strongest_pos: float
    strongest_neg: float
    strongest_pos_pair: Optional[List[int]]
    strongest_neg_pair: Optional[List[int]]


class ContestedPair(BaseModel):
    """A relation with low rating agreement (`results_insights_tab.py:417-446`)."""

    i: int
    j: int
    pair: str
    score: float
    agreement_ratio: float
    spread: float


class AgreementStats(BaseModel):
    """Rank agreement between decision-makers and the most contested relations (at most 5)."""

    average_agreement: float
    average_correlation: float
    contested: List[ContestedPair]


class HealthStats(BaseModel):
    """System health (`results_insights_tab.py:562-590`); integers."""

    score: int
    synergy: int
    conflict: int
    neutral_uncertain: int


class PolicyCardText(BaseModel):
    """Top driving / influenced policy card."""

    hero: str
    value_text: str


class StrongestLinkText(BaseModel):
    """Strongest Link card."""

    main: str
    value_text: str
    caption: str


class MostContestedText(BaseModel):
    """Most Contested card."""

    main: str
    value_text: str
    caption: str


class ConflictRatioText(BaseModel):
    """Conflict Ratio card."""

    ratio: float
    main_text: str
    value_text: str
    caption: str


class InsightsTexts(BaseModel):
    """Every displayed text, with label fixes L11-L14 applied."""

    story: str
    interpretation_label: str
    interpretation_text: str
    overview_agreement_text: str
    tag_top_driver: str
    tag_strongest_link: str
    tag_contested: str
    top_driver: PolicyCardText
    top_dependent: PolicyCardText
    strongest_link: StrongestLinkText
    most_contested: MostContestedText
    conflict_ratio: ConflictRatioText


class InsightsData(BaseModel):
    """Results Insights."""

    rows: List[InsightsRow]
    graph: GraphStats
    agreement: AgreementStats
    health: HealthStats
    texts: InsightsTexts
