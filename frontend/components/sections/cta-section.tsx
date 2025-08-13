'use client'

import React from 'react'
import Link from 'next/link'

export function CTASection() {
  return (
    <section className="py-20 max-w-7xl mx-auto px-6 text-center">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-4xl md:text-5xl font-bold text-primary mb-6 font-accent">
          Начните инвестировать уже сегодня
        </h2>
        <p className="text-lg text-neutral-dark/80 mb-10 leading-relaxed">
          Присоединяйтесь к тысячам инвесторов, которые уже используют Доходометр 
          для управления своими финансами и достижения финансовой независимости.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/auth/register">
            <button className="bg-accent-2 text-white px-10 py-4 rounded-xl text-lg font-semibold hover:bg-accent-2/90 transition-all hover:transform hover:scale-105 shadow-lg relative overflow-hidden group">
              <span className="relative z-10">Создать аккаунт бесплатно</span>
              <div className="absolute inset-0 bg-gradient-to-r from-accent-2 to-accent-1 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            </button>
          </Link>
          <Link href="/demo">
            <button className="border-2 border-primary text-primary px-10 py-4 rounded-xl text-lg font-semibold hover:bg-primary hover:text-white transition-all">
              Посмотреть демо
            </button>
          </Link>
        </div>
        
        {/* Статистика */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 pt-16 border-t border-neutral-light">
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-1 font-accent mb-2">
              10K+
            </div>
            <div className="text-sm text-neutral-dark/60">
              Активных пользователей
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-1 font-accent mb-2">
              ₽2.5M
            </div>
            <div className="text-sm text-neutral-dark/60">
              Средний портфель
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-1 font-accent mb-2">
              15.2%
            </div>
            <div className="text-sm text-neutral-dark/60">
              Средняя доходность
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-1 font-accent mb-2">
              99.9%
            </div>
            <div className="text-sm text-neutral-dark/60">
              Время работы
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
