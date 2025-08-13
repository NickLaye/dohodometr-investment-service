/**
 * Playwright global teardown.
 * 
 * This file runs once after all tests to clean up the testing environment,
 * including stopping test servers, cleaning up test data, etc.
 */

import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global test teardown...');

  try {
    // Clean up test data if needed
    await cleanupTestData();

    console.log('✅ Global teardown completed');

  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw here as we don't want to fail the test run
  }
}

async function cleanupTestData() {
  console.log('🗑️ Cleaning up test data...');

  // You can add any test data cleanup here
  // For example, removing test users, portfolios, etc.
  
  // Example cleanup operations:
  // - Clear test database
  // - Remove uploaded test files
  // - Reset test environment state

  console.log('✅ Test data cleanup completed');
}

export default globalTeardown;
