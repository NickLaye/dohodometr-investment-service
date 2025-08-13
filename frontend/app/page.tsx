'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
import { HeroSection } from '@/components/sections/hero-section'
import { BenefitsSection } from '@/components/sections/benefits-section'
import { DemoSection } from '@/components/sections/demo-section'
import { CTASection } from '@/components/sections/cta-section'
import { Footer } from '@/components/layout/footer'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-light to-white relative overflow-hidden">
      {/* Фоновая сетка */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <div 
          className="w-full h-full bg-repeat" 
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%231F3B35' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      <div className="relative z-10">
        <Header />
        <main>
          <HeroSection />
          <BenefitsSection />
          <DemoSection />
          <CTASection />
        </main>
        <Footer />
      </div>
    </div>
  )
}