import { useCallback, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AlertCircle, CheckCircle2, FileUp, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import PageHeader from '../components/PageHeader';
import { previewCsv, uploadCsv } from '../api/client';

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<{
    columns: string[];
    preview_rows: Record<string, string>[];
    total_rows: number;
  } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [progress, setProgress] = useState<'idle' | 'previewing' | 'uploading'>('idle');

  const handleFile = useCallback(async (f: File) => {
    setFile(f);
    setResult(null);
    setProgress('previewing');
    try {
      const data = await previewCsv(f);
      setPreview(data);
    } finally {
      setProgress('idle');
    }
  }, []);

  const uploadMutation = useMutation({
    mutationFn: uploadCsv,
    onMutate: () => setProgress('uploading'),
    onSuccess: (data) => {
      setResult(data);
      setProgress('idle');
    },
    onError: () => setProgress('idle'),
  });

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Veri İçe Aktarma"
        subtitle="MES CSV dosyasını yükleyin — otomatik validasyon ve özet rapor"
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={clsx('dropzone flex flex-col items-center justify-center', dragOver && 'dropzone-active')}
      >
        <div className="mb-4 rounded-2xl bg-white p-4 shadow-md">
          <FileUp className="text-indigo-500" size={44} />
        </div>
        <p className="mb-1 text-base font-semibold text-slate-700">CSV dosyasını sürükleyip bırakın</p>
        <p className="mb-4 text-sm text-slate-500">production_data.csv · max 18 kolon</p>
        <label className="btn-primary cursor-pointer">
          Dosya Seç
          <input
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </label>
        {file && <p className="mt-3 text-xs text-slate-500">{file.name}</p>}
      </div>

      {progress !== 'idle' && (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <Loader2 className="animate-spin" size={16} />
          {progress === 'previewing' ? 'Önizleme hazırlanıyor...' : 'Yükleniyor ve validate ediliyor...'}
        </div>
      )}

      {preview && (
        <div className="card">
          <h3 className="mb-3 font-semibold">Önizleme ({preview.total_rows} satır)</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  {preview.columns.slice(0, 8).map((c) => (
                    <th key={c} className="px-2 py-2 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.preview_rows.slice(0, 8).map((row, i) => (
                  <tr key={i} className="border-b border-slate-100">
                    {preview.columns.slice(0, 8).map((c) => (
                      <td key={c} className="max-w-[120px] truncate px-2 py-1.5">
                        {row[c]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            className="btn-primary mt-4"
            disabled={!file || uploadMutation.isPending}
            onClick={() => file && uploadMutation.mutate(file)}
          >
            {uploadMutation.isPending ? 'Yükleniyor...' : 'İçe Aktar & Validate Et'}
          </button>
        </div>
      )}

      {result && (
        <div className="card">
          <div className="mb-4 flex items-center gap-2">
            {result.duplicate ? (
              <AlertCircle className="text-amber-500" size={20} />
            ) : (
              <CheckCircle2 className="text-emerald-500" size={20} />
            )}
            <h3 className="font-semibold">
              {result.duplicate ? 'Duplicate Dosya Tespit Edildi' : 'İçe Aktarma Tamamlandı'}
            </h3>
          </div>
          {typeof result.summary === 'object' && result.summary !== null && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.entries(result.summary as Record<string, unknown>).map(([k, v]) =>
                typeof v === 'number' ? (
                  <div key={k} className="stat-chip">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{k}</p>
                    <p className="mt-1 text-2xl font-bold text-indigo-600">{v}</p>
                  </div>
                ) : null,
              )}
            </div>
          )}
          {typeof result.summary === 'object' &&
            result.summary !== null &&
            (result.summary as { issue_breakdown?: Record<string, number> }).issue_breakdown && (
              <div className="mt-4">
                <h4 className="mb-2 text-sm font-medium">Kalite Sorunları Dağılımı</h4>
                <div className="max-h-48 overflow-y-auto">
                  {Object.entries(
                    (result.summary as { issue_breakdown: Record<string, number> }).issue_breakdown,
                  )
                    .sort((a, b) => b[1] - a[1])
                    .map(([type, count]) => (
                      <div key={type} className="flex justify-between border-b border-slate-100 py-1 text-sm">
                        <span className="font-mono text-xs">{type}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}
        </div>
      )}
    </div>
  );
}
