import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface ProductionRecord {
  id: number;
  record_id: number;
  tarih: string;
  is_emri_no: string | null;
  is_merkezi_no: string | null;
  ismerkezi_adi: string | null;
  is_istasyon_adi: string | null;
  stok_adi: string | null;
  vardiya: number | null;
  availability: number | null;
  performance: number | null;
  quality: number | null;
  oee: number | null;
  calisma_suresi: number | null;
  durus_suresi: number | null;
  planli_durus: number | null;
  plansiz_durus: number | null;
  uretilen_miktar: number | null;
  hatali_miktar: number | null;
  validation_status: string;
}

export interface ValidationIssue {
  id: number;
  record_id: number;
  error_type: string;
  fields: string;
  message: string;
  severity: string;
  suggested_action: string;
  resolved: boolean;
}

export interface FilterOptions {
  stations: string[];
  products: string[];
  date_min: string | null;
  date_max: string | null;
}

export interface DashboardData {
  kpis: {
    avg_oee: number;
    total_production: number;
    total_scrap: number;
    total_downtime: number;
  };
  oee_trend: { date: string; avg_oee: number }[];
  shift_comparison: { shift: number; avg_oee: number; count: number }[];
  station_ranking: { station: string; avg_oee: number; count: number }[];
  scrap_distribution: { product: string; scrap_rate: number; production: number; scrap: number }[];
}

export const previewCsv = async (file: File) => {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/import/preview', form);
  return data;
};

export const uploadCsv = async (file: File) => {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/import', form);
  return data;
};

export const getValidationReport = async (batchId?: string) => {
  const { data } = await api.get('/import/validation', { params: { batch_id: batchId } });
  return data;
};

export const exportValidationReport = () => {
  window.open('/api/import/validation/export', '_blank');
};

export interface AuditLogEntry {
  id: number;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  action: string;
  created_at: string;
}

export const getRecordAudit = async (recordId: number) => {
  const { data } = await api.get<AuditLogEntry[]>(`/import/records/${recordId}/audit`);
  return data;
};

export const getRecords = async (params: Record<string, unknown>) => {
  const { data } = await api.get('/records', { params });
  return data as { total: number; records: ProductionRecord[] };
};

export const getFilters = async () => {
  const { data } = await api.get<FilterOptions>('/filters');
  return data;
};

export const getDashboard = async (params: Record<string, unknown>) => {
  const { data } = await api.get<DashboardData>('/dashboard', { params });
  return data;
};

export const updateRecord = async (recordId: number, body: Record<string, unknown>) => {
  const { data } = await api.patch(`/import/records/${recordId}`, body);
  return data;
};

export const exportRecords = (params: Record<string, unknown>) => {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
  });
  window.open(`/api/records/export?${qs.toString()}`, '_blank');
};

export const syncPreview = async () => {
  const { data } = await api.get('/sync/preview');
  return data;
};

export const triggerSync = async () => {
  const { data } = await api.post('/sync');
  return data as { job_id: string; status: string; message: string };
};

export const getSyncJobStatus = async (jobId: string) => {
  const { data } = await api.get(`/sync/jobs/${jobId}`);
  return data as {
    job_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    total: number;
    message: string;
    result?: Record<string, unknown>;
  };
};

export const getSyncHistory = async () => {
  const { data } = await api.get('/sync/history');
  return data;
};

export default api;
