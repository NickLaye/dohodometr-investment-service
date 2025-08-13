'use client'

import React from 'react'

export default function AppDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Обзор портфеля</h1>
        <p className="text-gray-600">
          Добро пожаловать в ваш личный кабинет Доходометр
        </p>
      </div>

      {/* Статистические карточки */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Общая стоимость
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  ₽1,245,780
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Доходность
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  +12.4%
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M21 18V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H19C20.1 3 21 3.9 21 5V18M12 7C9.24 7 7 9.24 7 12S9.24 17 12 17 17 14.76 17 12 14.76 7 12 7M12 9C13.66 9 15 10.34 15 12S13.66 15 12 15 9 13.66 9 12 10.34 9 12 9Z"/>
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Дивиденды
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  ₽24,560
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9L10,17Z"/>
                </svg>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Риск
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  Средний
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* График портфеля */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Динамика портфеля
        </h2>
        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">График портфеля будет здесь</p>
        </div>
      </div>

      {/* Последние транзакции */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Последние транзакции
        </h2>
        <div className="space-y-3">
          {[
            { type: 'buy', asset: 'SBER', amount: '+100 шт.', date: '2024-08-13', price: '₽25,500' },
            { type: 'sell', asset: 'GAZP', amount: '-50 шт.', date: '2024-08-12', price: '₹18,750' },
            { type: 'dividend', asset: 'LKOH', amount: 'Дивиденды', date: '2024-08-11', price: '₽2,340' },
          ].map((transaction, index) => (
            <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  transaction.type === 'buy' ? 'bg-green-100 text-green-600' :
                  transaction.type === 'sell' ? 'bg-red-100 text-red-600' :
                  'bg-blue-100 text-blue-600'
                }`}>
                  {transaction.type === 'buy' ? '+' : transaction.type === 'sell' ? '-' : '₽'}
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">{transaction.asset}</p>
                  <p className="text-sm text-gray-500">{transaction.amount}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{transaction.price}</p>
                <p className="text-sm text-gray-500">{transaction.date}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}