import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import ImportPage from './pages/ImportPage';
import RecordsPage from './pages/RecordsPage';
import SyncPage from './pages/SyncPage';
import ValidationPage from './pages/ValidationPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="import" element={<ImportPage />} />
            <Route path="validation" element={<ValidationPage />} />
            <Route path="records" element={<RecordsPage />} />
            <Route path="sync" element={<SyncPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
