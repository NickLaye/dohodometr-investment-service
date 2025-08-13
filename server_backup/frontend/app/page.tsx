import { redirect } from 'next/navigation'

export default function HomePage() {
  // Перенаправляем на демо налогового калькулятора
  redirect('/tax-demo')
}
