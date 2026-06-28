export interface TrendMetric {
  current: number;
  delta: number | null;
  pct: number | null;
}

export interface TrendCard {
  domain: string;
  artikel_recent: number;
  orwell: TrendMetric;
  bernays: TrendMetric;
}

export interface HeatmapRow {
  topic: string;
  cells: (number | null)[];
}

export interface TrendResponse {
  trend_cards: TrendCard[];
  topic_heatmap: { weeks: string[]; rows: HeatmapRow[] };
  domain_comparison: { domain: string; values: (number | null)[] }[];
  weeks: string[];
}

export interface DependencyScore {
  label: string;
  score: number | null;
  positiv: number;
  negativ: number;
  neutral: number;
  total: number;
}

export interface PublisherProfile {
  domain: string;
  artikel: number;
  stroemung: Record<string, number>;
  abhaengigkeit: Record<string, DependencyScore>;
}

export interface VerlaufEntry {
  date: string;
  count: number;
  orwell_median: number;
  orwell_max: number;
  bernays_median: number;
  bernays_max: number;
  dk_median?: number;
  dk_max?: number;
}

export interface DomainAverage {
  domain: string;
  artikel: number;
  orwell_avg: number;
  bernays_avg: number;
  dk_avg?: number;
}

export interface StatsResponse {
  total_articles: number;
  top_techniques: Record<string, number>;
  top_domains: Record<string, number>;
  top_stroemungen: Record<string, number>;
  orwell_distribution: Record<string, number | string>;
  bernays_distribution: Record<string, number | string>;
  dk_distribution?: Record<string, number | string> | null;
  domain_averages: DomainAverage[];
  sentiment_distribution: Record<string, number>;
}
