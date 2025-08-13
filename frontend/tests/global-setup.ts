/**
 * Playwright global setup.
 * 
 * This file runs once before all tests to set up the testing environment,
 * including starting test servers, setting up test data, etc.
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global test setup...');

  // Create a browser instance for setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Wait for the development server to be ready
    const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
    console.log(`⏳ Waiting for server at ${baseURL}...`);
    
    // Try to reach the server with retries
    let retries = 30;
    while (retries > 0) {
      try {
        const response = await page.goto(baseURL, { 
          timeout: 5000,
          waitUntil: 'domcontentloaded' 
        });
        
        if (response && response.ok()) {
          console.log('✅ Server is ready');
          break;
        }
      } catch (error) {
        retries--;
        if (retries === 0) {
          throw new Error(`Server at ${baseURL} is not responding after 30 attempts`);
        }
        console.log(`⏳ Server not ready, retrying... (${retries} attempts left)`);
        await page.waitForTimeout(1000);
      }
    }

    // Set up test data if needed
    await setupTestData(page);

    console.log('✅ Global setup completed');

  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

async function setupTestData(page: any) {
  console.log('📊 Setting up test data...');

  // You can add any test data setup here
  // For example, creating test users, portfolios, etc.
  
  // Example: Check if API is available
  try {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await page.request.get(`${apiBaseUrl}/health`);
    
    if (response.ok()) {
      console.log('✅ API server is responding');
    } else {
      console.warn('⚠️ API server is not responding, tests will use mocks');
    }
  } catch (error) {
    console.warn('⚠️ API server check failed, tests will use mocks');
  }

  console.log('✅ Test data setup completed');
}

export default globalSetup;
