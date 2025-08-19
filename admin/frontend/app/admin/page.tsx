import { AdminAPI } from '@/lib/api';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

export default async function AdminDashboardPage() {
  const data = await AdminAPI.dashboard();
  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Админка — Дашборд</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Агенты" value={data.agents} />
        <KpiCard title="Открытые задачи" value={data.tasks_open} />
        <KpiCard title="Открытые PR" value={data.prs_open} />
        <KpiCard title="Открытые риски" value={data.risks_open} />
      </div>
    </main>
  );
}

function KpiCard({ title, value }: { title: string; value: number }) {
  return (
    <Card>
      <CardHeader>{title}</CardHeader>
      <CardContent>{value}</CardContent>
    </Card>
  );
}


