import { AdminAPI } from '@/lib/api';
import { Table, Thead, Tbody, Tr, Th, Td } from '@/components/ui/table';

export default async function RisksPage() {
  const risks = await AdminAPI.risks();
  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Риски</h1>
      <Table>
        <Thead>
          <Tr>
            <Th>ID</Th>
            <Th>Название</Th>
            <Th>Уровень</Th>
            <Th>Статус</Th>
          </Tr>
        </Thead>
        <Tbody>
          {risks.map((r: any) => (
            <Tr key={r.id}>
              <Td>{r.id}</Td>
              <Td>{r.title}</Td>
              <Td>{r.level}</Td>
              <Td>{r.status}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </main>
  );
}


