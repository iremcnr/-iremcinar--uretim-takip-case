import { useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight, ChevronsUpDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';

export type SortDirection = 'asc' | 'desc';

export type DataTableColumn<T> = {
  key: string;
  label: string;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
  render?: (row: T) => React.ReactNode;
  className?: string;
  headerClassName?: string;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  rowKey: (row: T) => string | number;
  pageSize?: number;
  emptyMessage?: string;
  /** Server-side: toplam kayıt sayısı */
  total?: number;
  /** Server-side: kontrollü sayfa (1-based) */
  page?: number;
  onPageChange?: (page: number) => void;
  /** Server-side: kontrollü sıralama */
  sortKey?: string;
  sortDirection?: SortDirection;
  onSortChange?: (key: string, direction: SortDirection) => void;
  loading?: boolean;
};

const PAGE_SIZE = 10;

function compareValues(a: unknown, b: unknown): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b), 'tr', { numeric: true, sensitivity: 'base' });
}

function SortIcon({ active, direction }: { active: boolean; direction: SortDirection }) {
  if (!active) return <ChevronsUpDown size={14} className="text-slate-300" />;
  return direction === 'asc' ? (
    <ChevronUp size={14} className="text-blue-600" />
  ) : (
    <ChevronDown size={14} className="text-blue-600" />
  );
}

export default function DataTable<T>({
  columns,
  data,
  rowKey,
  pageSize = PAGE_SIZE,
  emptyMessage = 'Kayıt bulunamadı.',
  total,
  page: controlledPage,
  onPageChange,
  sortKey: controlledSortKey,
  sortDirection: controlledSortDirection,
  onSortChange,
  loading = false,
}: DataTableProps<T>) {
  const isServerMode = total !== undefined && onPageChange !== undefined;

  const [internalPage, setInternalPage] = useState(1);
  const [internalSortKey, setInternalSortKey] = useState<string | null>(null);
  const [internalSortDirection, setInternalSortDirection] = useState<SortDirection>('asc');

  const page = isServerMode ? (controlledPage ?? 1) : internalPage;
  const sortKey = isServerMode ? controlledSortKey : internalSortKey;
  const sortDirection: SortDirection = isServerMode
    ? (controlledSortDirection ?? 'asc')
    : internalSortDirection;

  const sortedData = useMemo(() => {
    if (isServerMode || !sortKey) return data;
    const column = columns.find((c) => c.key === sortKey);
    if (!column) return data;

    return [...data].sort((a, b) => {
      const av = column.sortValue ? column.sortValue(a) : (a as Record<string, unknown>)[column.key];
      const bv = column.sortValue ? column.sortValue(b) : (b as Record<string, unknown>)[column.key];
      const cmp = compareValues(av, bv);
      return sortDirection === 'asc' ? cmp : -cmp;
    });
  }, [columns, data, isServerMode, sortDirection, sortKey]);

  const totalItems = isServerMode ? total! : sortedData.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  useEffect(() => {
    if (!isServerMode && page > totalPages) setInternalPage(totalPages);
  }, [isServerMode, page, totalPages]);

  const pageData = isServerMode ? data : sortedData.slice((page - 1) * pageSize, page * pageSize);

  const handleSort = (key: string) => {
    const column = columns.find((c) => c.key === key);
    if (!column?.sortable) return;

    let nextKey = key;
    let nextDir: SortDirection = 'asc';

    if (sortKey === key) {
      nextDir = sortDirection === 'asc' ? 'desc' : 'asc';
    }

    if (isServerMode && onSortChange) {
      onSortChange(nextKey, nextDir);
      onPageChange?.(1);
      return;
    }

    setInternalSortKey(nextKey);
    setInternalSortDirection(nextDir);
    setInternalPage(1);
  };

  const goToPage = (next: number) => {
    const clamped = Math.min(Math.max(1, next), totalPages);
    if (isServerMode) onPageChange?.(clamped);
    else setInternalPage(clamped);
  };

  const rangeStart = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, totalItems);

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-600">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={clsx(
                    'px-3 py-2 font-medium',
                    col.sortable && 'cursor-pointer select-none hover:text-slate-700',
                    col.headerClassName,
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable && <SortIcon active={sortKey === col.key} direction={sortDirection} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-3 py-8 text-center text-slate-500">
                  Yükleniyor...
                </td>
              </tr>
            ) : pageData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-3 py-8 text-center text-slate-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              pageData.map((row) => (
                <tr key={rowKey(row)} className="border-b border-slate-100 hover:bg-slate-50">
                  {columns.map((col) => (
                    <td key={col.key} className={clsx('px-3 py-2', col.className)}>
                      {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalItems > 0 && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
          <p className="text-xs text-slate-500">
            {rangeStart}–{rangeEnd} / {totalItems} kayıt
          </p>
          <div className="flex items-center gap-1">
            <button
              type="button"
              className="rounded-lg border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-40"
              disabled={page <= 1}
              onClick={() => goToPage(page - 1)}
              aria-label="Önceki sayfa"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
              .reduce<(number | 'ellipsis')[]>((acc, p, idx, arr) => {
                if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push('ellipsis');
                acc.push(p);
                return acc;
              }, [])
              .map((item, idx) =>
                item === 'ellipsis' ? (
                  <span key={`e-${idx}`} className="px-1 text-slate-400">
                    …
                  </span>
                ) : (
                  <button
                    key={item}
                    type="button"
                    className={clsx(
                      'min-w-[2rem] rounded-lg px-2 py-1 text-xs font-medium',
                      page === item ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 hover:bg-indigo-50',
                    )}
                    onClick={() => goToPage(item)}
                  >
                    {item}
                  </button>
                ),
              )}
            <button
              type="button"
              className="rounded-lg border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50 disabled:opacity-40"
              disabled={page >= totalPages}
              onClick={() => goToPage(page + 1)}
              aria-label="Sonraki sayfa"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
