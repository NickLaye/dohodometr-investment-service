/**
 * Health Check API Route for Dohodometr Frontend
 * Used by Docker health checks and load balancers
 */

import { NextRequest, NextResponse } from 'next/server';

interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  environment: string;
  checks: Record<string, {
    status: 'healthy' | 'unhealthy' | 'warning' | 'not_available';
    details: string;
  }>;
  response_time_ms: number;
}

export async function GET(request: NextRequest): Promise<NextResponse<HealthCheck>> {
  const startTime = Date.now();
  
  const healthStatus: HealthCheck = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    checks: {},
    response_time_ms: 0,
  };

  // Backend API connectivity check
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Short timeout for health checks
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      const backendHealth = await response.json();
      healthStatus.checks.backend = {
        status: 'healthy',
        details: `Backend API responding (${response.status})`,
      };
      
      // Add backend checks summary
      if (backendHealth.checks) {
        const unhealthyBackendChecks = Object.entries(backendHealth.checks)
          .filter(([_, check]: [string, any]) => check.status === 'unhealthy')
          .map(([name]) => name);
          
        if (unhealthyBackendChecks.length > 0) {
          healthStatus.checks.backend = {
            status: 'warning',
            details: `Backend has unhealthy checks: ${unhealthyBackendChecks.join(', ')}`,
          };
        }
      }
    } else {
      healthStatus.checks.backend = {
        status: 'unhealthy',
        details: `Backend API error (${response.status})`,
      };
      healthStatus.status = 'unhealthy';
    }
  } catch (error) {
    healthStatus.checks.backend = {
      status: 'unhealthy',
      details: `Backend API connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    };
    healthStatus.status = 'unhealthy';
  }

  // Environment variables check
  const requiredEnvVars = [
    'NEXT_PUBLIC_API_URL',
  ];
  
  const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missingEnvVars.length === 0) {
    healthStatus.checks.environment = {
      status: 'healthy',
      details: 'All required environment variables are set',
    };
  } else {
    healthStatus.checks.environment = {
      status: 'warning',
      details: `Missing environment variables: ${missingEnvVars.join(', ')}`,
    };
    
    // Environment issues are usually not critical for basic functionality
    if (healthStatus.status === 'healthy') {
      healthStatus.status = 'degraded';
    }
  }

  // Next.js build check
  try {
    // Check if we're in a built environment
    const buildId = process.env.__NEXT_BUILD_ID || 'development';
    healthStatus.checks.build = {
      status: 'healthy',
      details: `Next.js build ID: ${buildId}`,
    };
  } catch (error) {
    healthStatus.checks.build = {
      status: 'warning',
      details: 'Build information not available',
    };
  }

  // Memory usage check (basic)
  try {
    const memoryUsage = process.memoryUsage();
    const heapUsedMB = Math.round(memoryUsage.heapUsed / 1024 / 1024);
    const heapTotalMB = Math.round(memoryUsage.heapTotal / 1024 / 1024);
    const heapUsagePercent = Math.round((heapUsedMB / heapTotalMB) * 100);
    
    if (heapUsagePercent < 90) {
      healthStatus.checks.memory = {
        status: 'healthy',
        details: `Heap usage: ${heapUsedMB}MB/${heapTotalMB}MB (${heapUsagePercent}%)`,
      };
    } else {
      healthStatus.checks.memory = {
        status: 'warning',
        details: `High heap usage: ${heapUsedMB}MB/${heapTotalMB}MB (${heapUsagePercent}%)`,
      };
      
      if (healthStatus.status === 'healthy') {
        healthStatus.status = 'degraded';
      }
    }
  } catch (error) {
    healthStatus.checks.memory = {
      status: 'not_available',
      details: 'Memory usage information not available',
    };
  }

  // Calculate response time
  healthStatus.response_time_ms = Date.now() - startTime;

  // Determine final status code
  const statusCode = healthStatus.status === 'unhealthy' ? 503 : 200;

  return NextResponse.json(healthStatus, { status: statusCode });
}

// Simple liveness check
export async function HEAD(): Promise<NextResponse> {
  return new NextResponse(null, { status: 200 });
}
