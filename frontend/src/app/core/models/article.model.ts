export interface DetectedTechnique {
  technique: string;
  quote: string;
  explanation: string;
}

export interface FramingTarget {
  main_narrative: string;
  intended_sentiment: string;
  orwell_index: number;
  dunning_kruger_index?: number;
  target_direction?: string;
}

export interface ArticleListItem {
  source_url: string;
  domain: string;
  title: string;
  published_at: string;
  orwell_index: number;
  bernays_score: number;
  dunning_kruger_index?: number;
  politische_stroemung: string[];
  technique_names: string[];
  intended_sentiment?: string;
}

export interface ManipulationTarget {
  entity: string;
  direction: 'positiv' | 'negativ' | 'neutral';
  direction_quote?: string | null;
  rolle: string;
  rolle_quote?: string | null;
}

export interface ArticleDetail extends ArticleListItem {
  author: string;
  word_count: number;
  timestamp: string;
  detected_techniques: DetectedTechnique[];
  framing_target: FramingTarget;
  themenbereich?: string;
  manipulation_targets?: ManipulationTarget[];
}

export interface ArticleFilter {
  domain?: string;
  orwell_min?: number;
  orwell_max?: number;
  limit?: number;
}
