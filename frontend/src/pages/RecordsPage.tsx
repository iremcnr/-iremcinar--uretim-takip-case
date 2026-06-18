import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import DataTable, { type SortDirection } from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import { exportRecords, getFilters, getRecords, type ProductionRecord } from '../api/client';
import clsx from 'clsx';

const statusBadge = (s: string) => {
  if (s === 'valid') return 'badge-valid';
  if (s === 'warning') return 'badge-warning';
  return 'badge-rejected';
};

const PAGE_SIZE = 10;

export default function RecordsPage() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [shifts, setShifts] = useState<number[]>([]);
  const [stations, setStations] = useState<string[]>([]);
  const [products, setProducts] = useState<string[]>([]);
  const [oeeMin, setOeeMin] = useState(0);
  const [oeeMax, setOeeMax] = useState(150);
  const [issuesOnly, setIssuesOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState('record_id');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const { data: filterOpts } = useQuery({ queryKey: ['filters'], queryFn: getFilters });

  const filterParams = useMemo(
    () => ({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      shifts: shifts.length ? shifts.join(',') : undefined,
      stations: stations.length ? stations.join(',') : undefined,
      products: products.length ? products.join(',') : undefined,
      oee_min: oeeMin > 0 ? oeeMin : undefined,
      oee_max: oeeMax < 150 ? oeeMax : undefined,
      issues_only: issuesOnly || undefined,
    }),
    [dateFrom, dateTo, shifts, stations, products, oeeMin, oeeMax, issuesOnly],
  );

  const queryParams = useMemo(
    () => ({
      ...filterParams,
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      sort_by: sortKey,
      sort_order: sortDirection,
    }),
    [filterParams, page, sortKey, sortDirection],
  );

  const { data, isLoading } = useQuery({
    queryKey: ['records', queryParams],
    queryFn: () => getRecords(queryParams),
  });

  const toggleShift = (s: number) => {
    setShifts((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
    setPage(1);
  };

  const columns = useMemo(
    () => [
      { key: 'record_id', label: 'ID', sortable: true, className: 'font-mono' },
      {
        key: 'tarih',
        label: 'Tarih',
        sortable: true,
        render: (r: ProductionRecord) => r.tarih?.slice(0, 10),
      },
      { key: 'is_istasyon_adi', label: 'İstasyon', sortable: true },
      {
        key: 'stok_adi',
        label: 'Ürün',
        sortable: true,
        className: 'max-w-[160px] truncate',
        render: (r: ProductionRecord) => r.stok_adi || '—',
      },
      { key: 'vardiya', label: 'Vardiya', sortable: true, render: (r: ProductionRecord) => r.vardiya ?? '—' },
      {
        key: 'oee',
        label: 'OEE',
        sortable: true,
        render: (r: ProductionRecord) => (r.oee != null ? r.oee.toFixed(1) : '—'),
      },
      { key: 'uretilen_miktar', label: 'Üretim', sortable: true },
      { key: 'hatali_miktar', label: 'Fire', sortable: true },
      {
        key: 'validation_status',
        label: 'Durum',
        sortable: true,
        render: (r: ProductionRecord) => (
          <span className={statusBadge(r.validation_status)}>{r.validation_status}</span>
        ),
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Kayıtlar & Filtreleme"
        subtitle={`${data?.total ?? 0} kayıt — çoklu filtre ve CSV export`}
        action={
          <button className="btn-secondary" onClick={() => exportRecords(filterParams)}>
            <Download size={16} /> CSV Dışa Aktar
          </button>
        }
      />

      <div className="filter-panel grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div>
          <label className="mb-1 block text-xs text-slate-500">Başlangıç Tarihi</label>
          <input
            type="date"
            className="input"
            value={dateFrom}
            min={filterOpts?.date_min?.slice(0, 10)}
            max={filterOpts?.date_max?.slice(0, 10)}
            onChange={(e) => {
              setDateFrom(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-500">Bitiş Tarihi</label>
          <input
            type="date"
            className="input"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-500">Vardiya</label>
          <div className="flex gap-2">
            {[1, 2, 3].map((s) => (
              <button
                key={s}
                onClick={() => toggleShift(s)}
                className={clsx(
                  'rounded-xl px-3 py-2 text-sm font-medium transition',
                  shifts.includes(s) ? 'bg-indigo-600 text-white shadow-md' : 'bg-white ring-1 ring-slate-200',
                )}
              >
                V{s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-500">İş İstasyonu</label>
          <select
            multiple
            className="input h-24"
            value={stations}
            onChange={(e) => {
              setStations(Array.from(e.target.selectedOptions, (o) => o.value));
              setPage(1);
            }}
          >
            {filterOpts?.stations.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-500">Ürün / Stok</label>
          <select
            multiple
            className="input h-24"
            value={products}
            onChange={(e) => {
              setProducts(Array.from(e.target.selectedOptions, (o) => o.value));
              setPage(1);
            }}
          >
            {filterOpts?.products.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-500">
            OEE Aralığı: {oeeMin} – {oeeMax}%
          </label>
          <input
            type="range"
            min={0}
            max={150}
            value={oeeMin}
            onChange={(e) => {
              setOeeMin(Number(e.target.value));
              setPage(1);
            }}
            className="w-full"
          />
          <input
            type="range"
            min={0}
            max={150}
            value={oeeMax}
            onChange={(e) => {
              setOeeMax(Number(e.target.value));
              setPage(1);
            }}
            className="mt-1 w-full"
          />
          <label className="mt-2 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={issuesOnly}
              onChange={(e) => {
                setIssuesOnly(e.target.checked);
                setPage(1);
              }}
            />
            Sadece sorunlu kayıtlar
          </label>
        </div>
      </div>

      <div className="card">
        <DataTable
          columns={columns}
          data={data?.records ?? []}
          rowKey={(r) => r.id}
          total={data?.total ?? 0}
          page={page}
          onPageChange={setPage}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSortChange={(key, dir) => {
            setSortKey(key);
            setSortDirection(dir);
            setPage(1);
          }}
          loading={isLoading}
          emptyMessage="Filtreye uygun kayıt bulunamadı."
        />
      </div>
    </div>
  );
}
