export interface AnalyseRequest {
  url: string;
  force?: boolean;
}

export interface AnalyseResponse {
  status: 'accepted' | 'skipped' | 'error';
  message: string;
  job_id: string | null;
}

export interface JobStatus {
  status: 'pending' | 'done' | 'error' | 'paywall';
  message?: string;
  result?: Record<string, unknown>;
}
