import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, RefreshCw, Send } from 'lucide-react';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import { getSyncHistory, getSyncJobStatus, syncPreview, triggerSync } from '../api/client';

type SyncPayload = {
  production_date: string;
  shift: number;
  machine_count: number;
  total_production_units: number;
  oe_value: number;
};

type SyncHistoryRow = {
  id: number;
  production_date: string;
  shift: number;
  oe_value: number;
  total_production_units: number;
  status: string;
  submission_id?: number | null;
};

export default function SyncPage() {
  const queryClient = useQueryClient();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [jobStatus, setJobStatus] = useState<{
    status: string;
    progress: number;
    total: number;
    message: string;
    result?: Record<string, unknown>;
  } | null>(null);

  const { data: preview } = useQuery({ queryKey: ['sync-preview'], queryFn: syncPreview });
  const { data: history } = useQuery({ queryKey: ['sync-history'], queryFn: getSyncHistory });

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollJob = useCallback(
    (id: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const status = await getSyncJobStatus(id);
          setJobStatus(status);
          if (status.status === 'completed' || status.status === 'failed') {
            stopPolling();
            queryClient.invalidateQueries({ queryKey: ['sync-history'] });
            queryClient.invalidateQueries({ queryKey: ['sync-preview'] });
          }
        } catch {
          stopPolling();
        }
      }, 800);
    },
    [queryClient, stopPolling],
  );

  useEffect(() => () => stopPolling(), [stopPolling]);

  const syncMutation = useMutation({
    mutationFn: triggerSync,
    onSuccess: (data) => {
      setJobStatus({ status: 'pending', progress: 0, total: 0, message: data.message });
      pollJob(data.job_id);
    },
  });

  const isRunning =
    syncMutation.isPending ||
    (jobStatus && !['completed', 'failed'].includes(jobStatus.status));

  const result = jobStatus?.status === 'completed' || jobStatus?.status === 'failed' ? jobStatus.result : null;

  const previewColumns = [
    { key: 'production_date', label: 'Tarih', sortable: true },
    { key: 'shift', label: 'Vardiya', sortable: true },
    { key: 'machine_count', label: 'Makine', sortable: true },
    { key: 'total_production_units', label: 'Üretim', sortable: true },
    { key: 'oe_value', label: 'OEE', sortable: true },
  ];

  const historyColumns = [
    { key: 'production_date', label: 'Tarih', sortable: true },
    { key: 'shift', label: 'Vardiya', sortable: true },
    { key: 'oe_value', label: 'OEE', sortable: true },
    { key: 'total_production_units', label: 'Üretim', sortable: true },
    {
      key: 'status',
      label: 'Durum',
      sortable: true,
      render: (h: SyncHistoryRow) => (
        <span className={h.status === 'success' ? 'badge-valid' : 'badge-rejected'}>{h.status}</span>
      ),
    },
    {
      key: 'submission_id',
      label: 'Submission ID',
      sortable: true,
      className: 'font-mono text-xs',
      render: (h: SyncHistoryRow) => h.submission_id ?? '—',
    },
  ];

  const previewData: SyncPayload[] = (preview?.payloads as SyncPayload[]) ?? [];
  const historyData: SyncHistoryRow[] = (history as SyncHistoryRow[]) ?? [];
  const progressPct =
    jobStatus && jobStatus.total > 0 ? Math.round((jobStatus.progress / jobStatus.total) * 100) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="API Senkronizasyon"
        subtitle="Temiz veriyi MAGNA hedef sistemine gönder — tarih + vardiya batch"
        action={
          <button className="btn-primary" disabled={!!isRunning} onClick={() => syncMutation.mutate()}>
            {isRunning ? (
              <>
                <Loader2 className="animate-spin" size={16} /> Gönderiliyor...
              </>
            ) : (
              <>
                <Send size={16} /> Senkronize Et
              </>
            )}
          </button>
        }
      />

      {isRunning && jobStatus && (
        <div className="card border-indigo-200 bg-gradient-to-r from-indigo-50 to-cyan-50">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-indigo-900">{jobStatus.message}</span>
            {jobStatus.total > 0 && (
              <span className="font-semibold text-indigo-700">
                {jobStatus.progress}/{jobStatus.total}
              </span>
            )}
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      )}

      <div className="card">
        <h3 className="mb-3 font-semibold">Gönderim Önizlemesi</h3>
        <p className="mb-3 text-sm text-slate-500">
          {preview?.count ?? 0} vardiya-gün batch'i hazır (sadece valid/warning kayıtlar)
        </p>
        <DataTable
          columns={previewColumns}
          data={previewData}
          rowKey={(row) => `${row.production_date}-${row.shift}`}
          emptyMessage="Gönderilecek batch bulunamadı."
        />
      </div>

      {result && (
        <div className={`card ${result.success ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
          <h3 className="mb-2 font-semibold">Gönderim Sonucu</h3>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-slate-500">Başarılı:</span> <strong>{result.success_count as number}</strong>
            </div>
            <div>
              <span className="text-slate-500">Başarısız:</span> <strong>{result.fail_count as number}</strong>
            </div>
            <div>
              <span className="text-slate-500">Atlanan:</span>{' '}
              <strong>{result.skipped_count as number}</strong>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="mb-3 flex items-center gap-2">
          <RefreshCw size={16} className="text-slate-400" />
          <h3 className="font-semibold">Gönderim Geçmişi</h3>
        </div>
        <DataTable
          columns={historyColumns}
          data={historyData}
          rowKey={(row) => row.id}
          emptyMessage="Henüz gönderim yapılmadı."
        />
      </div>
    </div>
  );
}
