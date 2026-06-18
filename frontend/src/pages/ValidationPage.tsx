import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import { exportValidationReport, getRecordAudit, getValidationReport, updateRecord, type ValidationIssue } from '../api/client';
import clsx from 'clsx';

const severityBadge = (s: string) => {
  if (s === 'reject') return 'badge-rejected';
  if (s === 'warn') return 'badge-warning';
  return 'badge-valid';
};

export default function ValidationPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'reject' | 'warn'>('all');
  const [editId, setEditId] = useState<number | null>(null);
  const [editField, setEditField] = useState('vardiya');
  const [editValue, setEditValue] = useState('');

  const { data: auditLogs } = useQuery({
    queryKey: ['audit', editId],
    queryFn: () => getRecordAudit(editId!),
    enabled: editId !== null,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['validation'],
    queryFn: () => getValidationReport(),
  });

  const fixMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) => updateRecord(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['validation'] });
      queryClient.invalidateQueries({ queryKey: ['records'] });
      setEditId(null);
    },
  });

  const issues: ValidationIssue[] = useMemo(() => {
    if (!data?.issues) return [];
    return data.issues.filter((i: ValidationIssue) =>
      filter === 'all' ? true : i.severity === filter,
    );
  }, [data?.issues, filter]);

  const columns = useMemo(
    () => [
      { key: 'record_id', label: 'record_id', sortable: true, className: 'font-mono' },
      {
        key: 'error_type',
        label: 'Hata Tipi',
        sortable: true,
        render: (issue: ValidationIssue) => (
          <span className={severityBadge(issue.severity)}>{issue.error_type}</span>
        ),
      },
      { key: 'fields', label: 'Alanlar', sortable: true, className: 'text-xs' },
      { key: 'message', label: 'Mesaj', sortable: true, className: 'max-w-xs text-xs text-slate-600' },
      { key: 'suggested_action', label: 'Aksiyon', sortable: true, className: 'text-xs' },
      {
        key: 'actions',
        label: 'İşlem',
        render: (issue: ValidationIssue) => (
          <div className="flex gap-1">
            <button
              className="text-xs text-blue-600 hover:underline"
              onClick={() => {
                setEditId(issue.record_id);
                setEditField(issue.fields.split(',')[0] || 'vardiya');
              }}
            >
              Düzelt
            </button>
            <button
              className="text-xs text-red-600 hover:underline"
              onClick={() => fixMutation.mutate({ id: issue.record_id, body: { action: 'reject' } })}
            >
              Reddet
            </button>
          </div>
        ),
      },
    ],
    [fixMutation],
  );

  if (isLoading) return <p className="text-slate-500">Validasyon raporu yükleniyor...</p>;
  if (!data?.issues?.length) return <p className="text-slate-500">Henüz validasyon sorunu yok veya veri import edilmedi.</p>;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Validasyon Raporu"
        subtitle={`${data.total_issues} kalite sorunu tespit edildi — reddet, uyar veya düzelt`}
        action={
          <div className="flex flex-wrap gap-2">
            <button className="btn-secondary" onClick={exportValidationReport}>
              <Download size={16} /> CSV İndir
            </button>
            {(['all', 'reject', 'warn'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={clsx(
                  'rounded-xl px-4 py-2 text-sm font-medium transition',
                  filter === f
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-md'
                    : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50',
                )}
              >
                {f === 'all' ? 'Tümü' : f === 'reject' ? 'Reddedilen' : 'Uyarı'}
              </button>
            ))}
          </div>
        }
      />

      {data.breakdown && (
        <div className="card">
          <h3 className="mb-3 font-semibold">Hata Tipi Dağılımı</h3>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
            {Object.entries(data.breakdown as Record<string, number>)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => (
                <div key={type} className="stat-chip border-l-4 border-indigo-400">
                  <p className="truncate font-mono text-xs text-slate-600">{type}</p>
                  <p className="text-lg font-bold">{count}</p>
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="card">
        <DataTable
          key={filter}
          columns={columns}
          data={issues}
          rowKey={(issue) => issue.id}
          emptyMessage="Bu filtrede sorun bulunamadı."
        />
      </div>

      {editId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="card w-full max-w-md">
            <h3 className="mb-4 font-semibold">Kayıt #{editId} Düzenle</h3>
            <div className="space-y-3">
              <select className="input" value={editField} onChange={(e) => setEditField(e.target.value)}>
                {['vardiya', 'stok_adi', 'is_emri_no', 'oee', 'uretilen_miktar', 'hatali_miktar'].map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              <input className="input" value={editValue} onChange={(e) => setEditValue(e.target.value)} />
              <div className="flex gap-2">
                <button
                  className="btn-primary"
                  onClick={() =>
                    fixMutation.mutate({
                      id: editId,
                      body: { [editField]: editValue, action: 'manual_fix' },
                    })
                  }
                >
                  Kaydet
                </button>
                <button className="btn-secondary" onClick={() => setEditId(null)}>
                  İptal
                </button>
              </div>
            </div>
            {auditLogs && auditLogs.length > 0 && (
              <div className="mt-4 border-t border-slate-100 pt-4">
                <h4 className="mb-2 text-sm font-medium text-slate-700">Düzeltme Geçmişi (Audit Trail)</h4>
                <div className="max-h-40 space-y-2 overflow-y-auto text-xs">
                  {auditLogs.map((log) => (
                    <div key={log.id} className="rounded-lg bg-slate-50 px-3 py-2">
                      <p className="font-medium text-slate-700">
                        {log.action} · {log.field_name}
                      </p>
                      <p className="text-slate-500">
                        {log.old_value ?? '—'} → {log.new_value ?? '—'}
                      </p>
                      <p className="text-slate-400">{new Date(log.created_at).toLocaleString('tr-TR')}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
