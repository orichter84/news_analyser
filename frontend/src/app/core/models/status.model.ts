export interface ServiceStatus {
  status: 'ok' | 'error';
  detail?: string;
}

export interface FeedStatus {
  running: boolean;
  pid: number | null;
  mode: string | null;
  started_at: string | null;
  last_run_at: string | null;
  last_run_status: string | null;
  last_run_articles: number | null;
  next_run_at: string | null;
}

export interface SystemStatus {
  backend: ServiceStatus;
  chroma: ServiceStatus;
  feed: FeedStatus;
}
