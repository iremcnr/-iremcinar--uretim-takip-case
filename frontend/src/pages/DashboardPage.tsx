import { useQuery } from '@tanstack/react-query';
import { Clock, Factory, Flame, Gauge } from 'lucide-react';
import ChartCard from '../components/ChartCard';
import PlotChart from '../components/PlotChart';
import KpiCard from '../components/KpiCard';
import PageHeader from '../components/PageHeader';
import { getDashboard } from '../api/client';
import { CHART_COLOR, CHART_COLOR_LIGHT, CHART_TEXT, buildTrendHighlightAnnotations, dashConfig, dashLayout, formatPercent } from '../lib/plotlyTheme';

export default function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: () => getDashboard({}) });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card text-center text-slate-500">
        Veri yok. Önce <strong>Veri İçe Aktarma</strong> sayfasından CSV yükleyin.
      </div>
    );
  }

  const trendDates = data.oee_trend.map((d) => d.date.slice(0, 10));
  const trendValues = data.oee_trend.map((d) => d.avg_oee);
  const trendAnnotations = buildTrendHighlightAnnotations(trendDates, trendValues);

  const shiftNames = data.shift_comparison.map((s) => `Vardiya ${s.shift}`);
  const shiftOee = data.shift_comparison.map((s) => s.avg_oee);

  const stationNames = data.station_ranking.map((s) => s.station);
  const stationOee = data.station_ranking.map((s) => s.avg_oee);

  const productNames = data.scrap_distribution.map((p) => p.product.slice(0, 18));
  const scrapRates = data.scrap_distribution.map((p) => p.scrap_rate);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Üretim Dashboard"
        subtitle="OEE metrikleri — günlük trend, vardiya ve istasyon analizi"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Ortalama OEE" value={data.kpis.avg_oee} suffix="%" icon={Gauge} variant="indigo" trend="Valid kayıtlar üzerinden" />
        <KpiCard label="Toplam Üretim" value={data.kpis.total_production.toLocaleString('tr-TR')} icon={Factory} variant="cyan" />
        <KpiCard label="Toplam Fire" value={data.kpis.total_scrap.toLocaleString('tr-TR')} icon={Flame} variant="amber" />
        <KpiCard label="Toplam Duruş" value={Math.round(data.kpis.total_downtime).toLocaleString('tr-TR')} suffix=" dk" icon={Clock} variant="rose" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="OEE Trendi" subtitle="Günlük ortalama — detay için noktanın üzerine gelin">
          <PlotChart
            data={[
              {
                x: trendDates,
                y: trendValues,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: CHART_COLOR, width: 2.5, shape: 'spline' },
                marker: { size: 5, color: CHART_COLOR, line: { width: 1, color: '#fff' } },
                hovertemplate: '<b>%{x}</b><br>OEE: %{y:.1f}%<extra></extra>',
              },
            ]}
            layout={{
              ...dashLayout,
              height: 340,
              margin: { t: 48, r: 24, b: 72, l: 56 },
              annotations: trendAnnotations,
              yaxis: { ...dashLayout.yaxis, range: [0, 105], dtick: 20, title: { text: 'OEE %', font: { size: 12, color: '#64748b' } } },
              xaxis: { ...dashLayout.xaxis, tickangle: -35, nticks: 6, tickformat: '%d.%m' },
            }}
            config={dashConfig}
            style={{ width: '100%' }}
            useResizeHandler
          />
        </ChartCard>

        <ChartCard title="Vardiya Performansı" subtitle="Vardiya bazlı OEE karşılaştırma">
          <PlotChart
            data={[
              {
                x: shiftNames,
                y: shiftOee,
                type: 'bar',
                text: shiftOee.map((v) => formatPercent(v)),
                textposition: 'outside',
                textfont: CHART_TEXT,
                cliponaxis: false,
                marker: { color: CHART_COLOR, line: { width: 0 } },
                hovertemplate: '%{x}<br>OEE: %{y:.1f}%<extra></extra>',
              },
            ]}
            layout={{
              ...dashLayout,
              height: 340,
              margin: { t: 32, r: 24, b: 56, l: 56 },
              yaxis: { ...dashLayout.yaxis, range: [0, 110], title: { text: 'OEE %', font: { size: 12, color: '#64748b' } } },
              bargap: 0.35,
            }}
            config={dashConfig}
            style={{ width: '100%' }}
            useResizeHandler
          />
        </ChartCard>

        <ChartCard title="İstasyon OEE Sıralaması" subtitle="Top 15 iş istasyonu">
          <PlotChart
            data={[
              {
                y: stationNames,
                x: stationOee,
                type: 'bar',
                orientation: 'h',
                text: stationOee.map((v) => formatPercent(v)),
                textposition: 'outside',
                textfont: CHART_TEXT,
                cliponaxis: false,
                marker: { color: CHART_COLOR_LIGHT, line: { width: 0 } },
                hovertemplate: '%{y}<br>OEE: %{x:.1f}%<extra></extra>',
              },
            ]}
            layout={{
              ...dashLayout,
              height: 420,
              margin: { t: 16, r: 64, b: 48, l: 120 },
              xaxis: { ...dashLayout.xaxis, range: [0, 110], title: { text: 'OEE %', font: { size: 12, color: '#64748b' } } },
              yaxis: { ...dashLayout.yaxis, automargin: true },
            }}
            config={dashConfig}
            style={{ width: '100%' }}
            useResizeHandler
          />
        </ChartCard>

        <ChartCard title="Fire Oranı Dağılımı" subtitle="Top 10 ürün — scrap rate">
          <PlotChart
            data={[
              {
                x: productNames,
                y: scrapRates,
                type: 'bar',
                text: scrapRates.map((v) => formatPercent(v, 2)),
                textposition: 'outside',
                textfont: CHART_TEXT,
                cliponaxis: false,
                marker: { color: '#94a3b8', line: { width: 0 } },
                hovertemplate: '%{x}<br>Fire: %{y:.2f}%<extra></extra>',
              },
            ]}
            layout={{
              ...dashLayout,
              height: 420,
              margin: { t: 32, r: 24, b: 100, l: 56 },
              xaxis: { ...dashLayout.xaxis, tickangle: -40 },
              yaxis: { ...dashLayout.yaxis, title: { text: 'Fire %', font: { size: 12, color: '#64748b' } } },
            }}
            config={dashConfig}
            style={{ width: '100%' }}
            useResizeHandler
          />
        </ChartCard>
      </div>
    </div>
  );
}
