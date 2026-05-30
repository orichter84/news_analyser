from __future__ import annotations

from pydantic import BaseModel


class DistributionStats(BaseModel):
    mean: float
    median: float
    std: float | None = None
    min: float
    max: float


class OrwellDistribution(DistributionStats):
    pass


class BernaysDistribution(BaseModel):
    mean: float
    median: float
    max: float
    min: float


class DKDistribution(DistributionStats):
    bescheiden: int
    moderat: int
    ueberzeugt: int


class DomainAverage(BaseModel):
    domain: str
    artikel: int
    orwell_avg: float
    bernays_avg: float
    dk_avg: float | None = None


class StatsResponse(BaseModel):
    total_articles: int
    top_techniques: dict[str, int]
    top_domains: dict[str, int]
    top_stroemungen: dict[str, int]
    orwell_distribution: dict
    bernays_distribution: dict
    dk_distribution: dict | None = None
    domain_averages: list[DomainAverage]
    sentiment_distribution: dict[str, int]
