export interface VerlaufEntry {
  date: string;
  count: number;
  orwell_median: number;
  bernays_median: number;
  dk_median?: number;
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
