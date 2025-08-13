'use client'

import React from 'react'
import Link from 'next/link'

export function Header() {
  return (
    <header className="flex justify-between items-center py-6 max-w-7xl mx-auto px-6">
      <Link href="/" className="flex items-center gap-3">
        <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
          <svg className="w-6 h-6 text-neutral-light" fill="currentColor" viewBox="0 0 24 24">
            <path d="M3 3v18h18V3H3zm16 16H5V5h14v14z"/>
            <path d="M7 12l2 2 4-4 4 4V9l-4-4-4 4-2-2z"/>
          </svg>
        </div>
        <span className="text-2xl font-bold text-primary font-accent">Доходометр</span>
      </Link>

      <nav className="hidden md:flex items-center gap-8">
        <Link href="/" className="text-primary hover:text-accent-2 transition-colors font-medium">
          Главная
        </Link>
        <Link href="/features" className="text-primary hover:text-accent-2 transition-colors font-medium">
          Функции
        </Link>
        <Link href="/pricing" className="text-primary hover:text-accent-2 transition-colors font-medium">
          Тарифы
        </Link>
        <Link href="/contact" className="text-primary hover:text-accent-2 transition-colors font-medium">
          Контакты
        </Link>
      </nav>

      <div className="flex items-center gap-4">
        <button className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center hover:bg-primary/20 transition-colors">
          <svg className="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/>
          </svg>
        </button>
        <Link href="/auth/login">
          <button className="bg-accent-2 text-white px-6 py-2 rounded-lg hover:bg-accent-2/90 transition-colors font-medium">
            Войти
          </button>
        </Link>
      </div>
    </header>
  )
}
