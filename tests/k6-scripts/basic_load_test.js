// 🛡️ SECURE AI STUDIO - Basic k6 Load Test Script
// Test basic API functionality and response times

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const generationDuration = new Trend('generation_duration');
const errorCount = new Counter('errors');
const successRate = new Rate('success_rate');

// Test configuration
export const options = {
  scenarios: {
    constant_load: {
      executor: 'constant-vus',
      vus: 10,
      duration: '2m',
      gracefulStop: '30s',
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<10000'],  // 95% of requests under 10s
    http_req_failed: ['rate<0.02'],      // Error rate under 2%
    success_rate: ['rate>0.95'],         // 95% success rate
    generation_duration: ['p(90)<8000'], // 90% under 8s
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Test data
const testPrompts = [
  'A beautiful landscape painting',
  'Corporate logo design',
  'Abstract art composition',
  'Photorealistic portrait',
  'Minimalist geometric design'
];

const testResolutions = [
  [256, 256],
  [512, 512],
  [1024, 1024]
];

export function setup() {
  // Verify API is accessible
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error(`API not accessible: ${res.status}`);
  }
  
  console.log(`🚀 Starting load test against ${BASE_URL}`);
  return { test_start: Date.now() };
}

export default function () {
  group('API Health Check', function () {
    const res = http.get(`${BASE_URL}/health`);
    check(res, {
      'health check status is 200': (r) => r.status === 200,
      'response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    successRate.add(res.status === 200);
    if (res.status !== 200) errorCount.add(1);
    
    sleep(0.5);
  });

  group('Content Generation', function () {
    // Random test parameters
    const prompt = testPrompts[Math.floor(Math.random() * testPrompts.length)];
    const resolution = testResolutions[Math.floor(Math.random() * testResolutions.length)];
    const batchSize = Math.floor(Math.random() * 3) + 1; // 1-3
    
    const payload = {
      content_type: 'image',
      prompt: prompt,
      dimensions: resolution,
      format: 'PNG',
      quality: 'HIGH',
      batch_size: batchSize,
      priority: 'normal'
    };

    const startTime = new Date().getTime();
    
    const res = http.post(
      `${BASE_URL}/generate`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '30s',
      }
    );

    const duration = new Date().getTime() - startTime;
    generationDuration.add(duration);

    const checks = {
      'generation status is 200': (r) => r.status === 200,
      'response time < 30s': () => duration < 30000,
      'has job ID': (r) => {
        if (r.status === 200) {
          const body = JSON.parse(r.body);
          return body.job_id && body.job_id.length > 0;
        }
        return false;
      },
      'has output paths': (r) => {
        if (r.status === 200) {
          const body = JSON.parse(r.body);
          return body.output_paths && body.output_paths.length > 0;
        }
        return false;
      }
    };

    const result = check(res, checks);
    successRate.add(result);
    
    if (!result) {
      errorCount.add(1);
      console.log(`❌ Generation failed: ${res.status}, Duration: ${duration}ms`);
    } else {
      console.log(`✅ Generation successful: ${duration}ms, Batch: ${batchSize}`);
    }
  });

  // Random pause between iterations
  sleep(Math.random() * 2 + 1);
}

export function teardown(data) {
  console.log(`🏁 Load test completed. Duration: ${(Date.now() - data.test_start) / 1000}s`);
  
  // Get final metrics
  const metrics_res = http.get(`${BASE_URL}/metrics/performance`);
  if (metrics_res.status === 200) {
    const metrics = JSON.parse(metrics_res.body);
    console.log(`📊 Final Performance - CPU: ${metrics.cpu_percent}%, Memory: ${metrics.memory_percent}%`);
  }
}