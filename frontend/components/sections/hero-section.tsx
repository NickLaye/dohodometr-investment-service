'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'

export function HeroSection() {
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    setIsLoaded(true)
    
    // Анимация микро-диаграмм
    setTimeout(() => {
      const microBars = document.querySelectorAll('.micro-bar')
      microBars.forEach((bar, index) => {
        setTimeout(() => {
          const element = bar as HTMLElement
          element.style.height = element.dataset.height || '0%'
        }, index * 100)
      })
    }, 500)
  }, [])

  return (
    <section className="py-20 max-w-7xl mx-auto px-6">
      <div className="grid md:grid-cols-2 gap-12 items-center">
        <div className={`space-y-6 ${isLoaded ? 'animate-fadeInUp' : 'opacity-0'}`}>
          <h1 className="text-5xl md:text-6xl font-bold text-primary leading-tight font-accent">
            Управляйте финансами с умом
          </h1>
          <p className="text-lg text-neutral-dark/80 leading-relaxed">
            Доходометр — это современный инструмент для анализа и планирования личных финансов. 
            Отслеживайте доходы, оптимизируйте расходы и достигайте финансовых целей.
          </p>
          <Link href="/auth/register">
            <button className="bg-accent-2 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-accent-2/90 transition-all hover:transform hover:scale-105 shadow-lg">
              Начать бесплатно
            </button>
          </Link>
        </div>

        <div className={`relative ${isLoaded ? 'animate-fadeInRight' : 'opacity-0'}`}>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-neutral-light">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-3 h-3 bg-red-400 rounded-full"></div>
              <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
              <div className="w-3 h-3 bg-green-400 rounded-full"></div>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-dark/60">Портфель</span>
                <span className="text-accent-1 font-semibold font-accent">₽1,245,780</span>
              </div>
              <div className="h-32 flex items-end justify-between gap-2">
                {[70, 40, 90, 60, 80, 50, 100, 75, 95, 65].map((height, i) => (
                  <div 
                    key={i}
                    className="micro-bar bg-gradient-to-t from-accent-2 to-accent-1 rounded-t flex-1 transition-all duration-1000 ease-out"
                    data-height={`${height}%`}
                    style={{ height: '0%' }}
                  />
                ))}
              </div>
              <div className="pt-4 border-t border-neutral-light/50">
                <div className="flex justify-between text-xs text-neutral-dark/60">
                  <span>Янв</span>
                  <span>Дек</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fadeInRight {
          from {
            opacity: 0;
            transform: translateX(30px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .animate-fadeInUp {
          animation: fadeInUp 1s ease-out forwards;
        }

        .animate-fadeInRight {
          animation: fadeInRight 1s ease-out 0.3s forwards;
        }
      `}</style>
    </section>
  )
}
