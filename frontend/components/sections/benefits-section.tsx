'use client'

import React, { useState, useEffect } from 'react'

export function BenefitsSection() {
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    setIsLoaded(true)
    
    // Анимация микро-диаграмм в карточках
    setTimeout(() => {
      const microBars = document.querySelectorAll('.benefit-micro-bar')
      microBars.forEach((bar, index) => {
        setTimeout(() => {
          const element = bar as HTMLElement
          element.style.height = element.dataset.height || '0%'
        }, index * 50)
      })
    }, 1000)
  }, [])

  const benefits = [
    {
      icon: (
        <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 3v18h18V3H3zm16 16H5V5h14v14z"/>
          <path d="M7 12l2 2 4-4 4 4V9l-4-4-4 4-2-2z"/>
        </svg>
      ),
      title: "Финансовая аналитика",
      description: "Получайте детальные отчеты о движении средств, анализируйте тренды и оптимизируйте бюджет.",
      bars: [70, 40, 90, 60, 80, 50, 100]
    },
    {
      icon: (
        <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
      ),
      title: "Умные уведомления",
      description: "Система оповещений о важных финансовых событиях, платежах и достижении целей.",
      bars: [60, 80, 50, 90, 40, 70, 85]
    },
    {
      icon: (
        <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9L10,17Z"/>
        </svg>
      ),
      title: "Безопасность данных",
      description: "Шифрование банковского уровня и многофакторная аутентификация для защиты ваших финансовых данных.",
      bars: [90, 95, 85, 100, 92, 88, 97]
    }
  ]

  return (
    <section className="py-20 max-w-7xl mx-auto px-6">
      <h2 className="text-4xl font-bold text-center text-primary mb-16 font-accent">
        Преимущества сервиса
      </h2>
      
      <div className="grid md:grid-cols-3 gap-8">
        {benefits.map((benefit, index) => (
          <div 
            key={index}
            className={`bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 hover:transform hover:-translate-y-1 border border-neutral-light ${isLoaded ? 'animate-fadeInUp' : 'opacity-0'}`}
            style={{ animationDelay: `${index * 200}ms` }}
          >
            <div className="text-accent-2 mb-6 transform hover:rotate-6 transition-transform duration-300">
              {benefit.icon}
            </div>
            <h3 className="text-xl font-bold text-primary mb-4 font-accent">
              {benefit.title}
            </h3>
            <p className="text-neutral-dark/80 mb-6 leading-relaxed">
              {benefit.description}
            </p>
            <div className="h-10 flex items-end justify-between gap-1">
              {benefit.bars.map((height, i) => (
                <div 
                  key={i}
                  className="benefit-micro-bar bg-gradient-to-t from-accent-2 to-accent-1 rounded-t w-2 transition-all duration-1000 ease-out"
                  data-height={`${height}%`}
                  style={{ height: '0%' }}
                />
              ))}
            </div>
          </div>
        ))}
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

        .animate-fadeInUp {
          animation: fadeInUp 1s ease-out forwards;
        }
      `}</style>
    </section>
  )
}
