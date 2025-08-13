'use client'

import React, { useState } from 'react'

export function DemoSection() {
  const [currentSliderValue, setCurrentSliderValue] = useState(100000)

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  const calculateResult = () => {
    return Math.round(currentSliderValue * 1.15) // Простая формула для демо
  }

  return (
    <section className="py-20 max-w-7xl mx-auto px-6">
      <h2 className="text-4xl font-bold text-center text-primary mb-16 font-accent">
        Попробуйте в действии
      </h2>
      
      <div className="max-w-4xl mx-auto bg-white/80 backdrop-blur-sm rounded-3xl p-10 shadow-xl border border-neutral-light relative overflow-hidden">
        {/* Декоративный элемент */}
        <div className="absolute top-0 right-0 w-60 h-60 bg-gradient-to-br from-accent-2/10 to-accent-1/10 rounded-full -translate-y-20 translate-x-20"></div>
        
        <div className="relative z-10">
          <h3 className="text-2xl font-bold text-primary mb-8 font-accent">
            Калькулятор инвестиций
          </h3>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-neutral-dark mb-2">
                  Начальная сумма
                </label>
                <div className="relative">
                  <input
                    type="range"
                    min="10000"
                    max="1000000"
                    step="10000"
                    value={currentSliderValue}
                    onChange={(e) => setCurrentSliderValue(Number(e.target.value))}
                    className="w-full h-2 bg-gradient-to-r from-accent-2 to-accent-1 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-sm text-neutral-dark/60 mt-2">
                    <span>₽10,000</span>
                    <span>₽1,000,000</span>
                  </div>
                </div>
                <div className="text-center mt-4">
                  <span className="text-3xl font-bold text-primary font-accent">
                    ₽{formatNumber(currentSliderValue)}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-dark mb-2">
                    Срок инвестирования
                  </label>
                  <select className="w-full p-3 border border-neutral-light rounded-lg bg-white/80 backdrop-blur-sm">
                    <option value="1">1 год</option>
                    <option value="3">3 года</option>
                    <option value="5">5 лет</option>
                    <option value="10">10 лет</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-dark mb-2">
                    Уровень риска
                  </label>
                  <div className="flex gap-2">
                    <button className="flex-1 p-2 text-sm bg-accent-2/20 text-accent-2 rounded-lg hover:bg-accent-2/30 transition-colors">
                      Низкий
                    </button>
                    <button className="flex-1 p-2 text-sm bg-accent-1 text-white rounded-lg">
                      Средний
                    </button>
                    <button className="flex-1 p-2 text-sm bg-accent-2/20 text-accent-2 rounded-lg hover:bg-accent-2/30 transition-colors">
                      Высокий
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="bg-primary/5 rounded-xl p-6 text-center">
                <div className="text-sm text-neutral-dark/60 mb-2">
                  Прогноз через год
                </div>
                <div className="text-3xl font-bold text-accent-1 font-accent">
                  ₽{formatNumber(calculateResult())}
                </div>
                <div className="text-sm text-accent-2 mt-2">
                  +15% доходность
                </div>
              </div>

              <div className="bg-white/60 rounded-xl p-6">
                <h4 className="font-semibold text-primary mb-4">Распределение портфеля:</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Акции</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-neutral-light rounded-full overflow-hidden">
                        <div className="h-full bg-accent-2 rounded-full" style={{ width: '60%' }}></div>
                      </div>
                      <span className="text-sm font-medium">60%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Облигации</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-neutral-light rounded-full overflow-hidden">
                        <div className="h-full bg-accent-1 rounded-full" style={{ width: '30%' }}></div>
                      </div>
                      <span className="text-sm font-medium">30%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Денежные средства</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-neutral-light rounded-full overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: '10%' }}></div>
                      </div>
                      <span className="text-sm font-medium">10%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <style jsx>{`
          .slider::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #63B8A7;
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
          }

          .slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #63B8A7;
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
          }
        `}</style>
      </div>
    </section>
  )
}
