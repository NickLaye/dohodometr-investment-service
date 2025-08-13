'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const navigationItems = [
  {
    href: '/app',
    label: 'Обзор',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
      </svg>
    )
  },
  {
    href: '/app/portfolio',
    label: 'Портфель',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    )
  },
  {
    href: '/app/transactions',
    label: 'Транзакции',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M7 4V2C7 1.45 7.45 1 8 1S9 1.45 9 2V4H15V2C15 1.45 15.45 1 16 1S17 1.45 17 2V4H20C21.1 4 22 4.9 22 6V20C22 21.1 21.1 22 20 22H4C2.9 22 2 21.1 2 20V6C2 4.9 2.9 4 4 4H7M4 8H20V20H4V8Z"/>
      </svg>
    )
  },
  {
    href: '/app/analytics',
    label: 'Аналитика',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M22 21H2V3H4V19H6V17H10V19H12V16H16V19H18V18H22V21M16 8H18V15H16V8M12 2H14V15H12V2M8 9H10V15H8V9M4 12H6V15H4V12Z"/>
      </svg>
    )
  }
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Логотип */}
      <div className="p-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 3v18h18V3H3zm16 16H5V5h14v14z"/>
              <path d="M7 12l2 2 4-4 4 4V9l-4-4-4 4-2-2z"/>
            </svg>
          </div>
          <span className="text-xl font-bold text-primary font-accent">Доходометр</span>
        </Link>
      </div>

      {/* Навигация */}
      <nav className="flex-1 px-4">
        <ul className="space-y-2">
          {navigationItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  pathname === item.href
                    ? "bg-primary text-white"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
              >
                {item.icon}
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}