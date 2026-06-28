import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ArticleListItem, ArticleDetail, ArticleFilter } from '../models/article.model';
import { StatsResponse, VerlaufEntry, PublisherProfile } from '../models/stats.model';
import { AnalyseRequest, AnalyseResponse, JobStatus } from '../models/analyse.model';
import { Technique } from '../models/technique.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly base = `http://${window.location.hostname}:8000`;
  private readonly http = inject(HttpClient);

  getArticles(filter?: ArticleFilter): Observable<ArticleListItem[]> {
    let params = new HttpParams();
    if (filter?.domain) params = params.set('domain', filter.domain);
    if (filter?.orwell_min != null) params = params.set('orwell_min', filter.orwell_min);
    if (filter?.orwell_max != null) params = params.set('orwell_max', filter.orwell_max);
    if (filter?.limit) params = params.set('limit', filter.limit);
    return this.http.get<ArticleListItem[]>(`${this.base}/articles`, { params });
  }

  getArticle(url: string): Observable<ArticleDetail> {
    return this.http.get<ArticleDetail>(`${this.base}/articles/${encodeURIComponent(url)}`);
  }

  getStats(): Observable<StatsResponse> {
    return this.http.get<StatsResponse>(`${this.base}/stats`);
  }

  getPublisherProfiles(): Observable<PublisherProfile[]> {
    return this.http.get<PublisherProfile[]>(`${this.base}/stats/publisher`);
  }

  getVerlauf(domain?: string): Observable<VerlaufEntry[]> {
    let params = new HttpParams();
    if (domain) params = params.set('domain', domain);
    return this.http.get<VerlaufEntry[]>(`${this.base}/stats/verlauf`, { params });
  }

  submitAnalyse(req: AnalyseRequest): Observable<AnalyseResponse> {
    return this.http.post<AnalyseResponse>(`${this.base}/analyse`, req);
  }

  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.base}/analyse/job/${jobId}`);
  }

  search(q: string, n = 5): Observable<(ArticleListItem & { similarity: number })[]> {
    const params = new HttpParams().set('q', q).set('n', n);
    return this.http.get<(ArticleListItem & { similarity: number })[]>(`${this.base}/search`, { params });
  }

  getTechniques(): Observable<Technique[]> {
    return this.http.get<Technique[]>(`${this.base}/techniques`);
  }

  getTechnique(id: string): Observable<Technique> {
    return this.http.get<Technique>(`${this.base}/techniques/${id}`);
  }

  getConfig(): Observable<{ submit_enabled: boolean }> {
    return this.http.get<{ submit_enabled: boolean }>(`${this.base}/config`);
  }
}
