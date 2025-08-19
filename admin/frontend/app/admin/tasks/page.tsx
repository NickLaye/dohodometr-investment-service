import { AdminAPI } from '@/lib/api';
import { Table, Thead, Tbody, Tr, Th, Td } from '@/components/ui/table';

export default async function TasksPage() {
  const tasks = await AdminAPI.tasks();
  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Задачи</h1>
      <Table>
        <Thead>
          <Tr>
            <Th>ID</Th>
            <Th>Название</Th>
            <Th>Статус</Th>
          </Tr>
        </Thead>
        <Tbody>
          {tasks.map((t: any) => (
            <Tr key={t.id}>
              <Td>{t.id}</Td>
              <Td>{t.title}</Td>
              <Td>{t.status}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </main>
  );
}


