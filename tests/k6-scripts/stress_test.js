// 🛡️ SECURE AI STUDIO - Stress Test Script
// High-concurrency stress testing to identify breaking points

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Gauge, Rate, Trend } from 'k6/metrics';

// Custom metrics
const generationTime = new Trend('generation_time');
const concurrentUsers = new Gauge('concurrent_users');
const errorRate = new Rate('error_rate');
const throughput = new Counter('requests_total');

export const options = {
  scenarios: {
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 20 },   // Ramp up to 20 users
        { duration: '2m', target: 50 },    // Hold at 50 users
        { duration: '30s', target: 100 },  // Spike to 100 users
        { duration: '1m', target: 100 },   // Hold at 100 users
        { duration: '30s', target: 0 },    // Ramp down
      ],
      gracefulRampDown: '30s',
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<25000'],  // 95% under 25s
    http_req_failed: ['rate<0.05'],      // Less than 5% errors
    generation_time: ['p(90)<20000'],    // 90% under 20s
    error_rate: ['rate<0.1'],            // Error rate under 10%
    checks: ['rate>0.9'],                // 90% check pass rate
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Complex test scenarios
const complexPrompts = [
  'Hyperrealistic portrait of a person with intricate details, professional lighting, 8k resolution',
  'Fantasy landscape with mountains, rivers, and magical creatures, cinematic composition',
  'Corporate headquarters building with modern architecture, blue sky, professional photography',
  'Abstract digital art with geometric patterns, vibrant colors, contemporary style',
  'Historical castle surrounded by mist, dramatic lighting, oil painting style'
];

const resolutions = [
  [256, 256],   // Small
  [512, 512],   // Medium
  [1024, 1024], // Large
  [2048, 2048]  // Extra large
];

const qualities = ['LOW', 'MEDIUM', 'HIGH'];
const batchSizes = [1, 2, 3, 5];

export function setup() {
  // Verify system health before stress test
  const health_res = http.get(`${BASE_URL}/health`);
  if (health_res.status !== 200) {
    throw new Error(`System not healthy: ${health_res.status}`);
  }
  
  const system_res = http.get(`${BASE_URL}/system/status`);
  console.log(`💪 Starting stress test. System status: ${system_res.status}`);
  
  return { start_time: Date.now() };
}

export default function () {
  const vu_id = __VU;
  concurrentUsers.add(vu_id);
  throughput.add(1);
  
  group('System Health Monitoring', function () {
    // Check system health periodically
    if (__ITER % 10 === 0) {  // Every 10 iterations
      const health_res = http.get(`${BASE_URL}/health`);
      check(health_res, {
        'system health check passes': (r) => r.status === 200,
      });
      
      // Get performance metrics
      const perf_res = http.get(`${BASE_URL}/metrics/performance`);
      if (perf_res.status === 200) {
        const metrics = JSON.parse(perf_res.body);
        console.log(`📊 VU ${vu_id}: CPU ${metrics.cpu_percent}%, Memory ${metrics.memory_percent}%`);
      }
    }
  });

  group('Stress Generation Request', function () {
    // Complex randomized request
    const prompt = complexPrompts[Math.floor(Math.random() * complexPrompts.length)];
    const resolution = resolutions[Math.floor(Math.random() * resolutions.length)];
    const quality = qualities[Math.floor(Math.random() * qualities.length)];
    const batchSize = batchSizes[Math.floor(Math.random() * batchSizes.length)];
    
    // Higher chance of complex requests under stress
    const complexity_multiplier = Math.random() > 0.7 ? 2 : 1;
    const finalBatchSize = Math.min(batchSize * complexity_multiplier, 5);

    const payload = {
      content_type: 'image',
      prompt: prompt,
      dimensions: resolution,
      format: 'PNG',
      quality: quality,
      batch_size: finalBatchSize,
      priority: 'normal'
    };

    const startTime = new Date().getTime();
    
    const res = http.post(
      `${BASE_URL}/generate`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '60s',  // Longer timeout for stress conditions
      }
    );

    const duration = new Date().getTime() - startTime;
    generationTime.add(duration);
    errorRate.add(res.status !== 200);

    const checks = {
      'request completed': (r) => r.status === 200 || r.status === 503, // 503 is acceptable under stress
      'response time acceptable': () => duration < 60000,
      'proper response format': (r) => {
        if (r.status === 200) {
          try {
            const body = JSON.parse(r.body);
            return body.hasOwnProperty('success') && body.hasOwnProperty('job_id');
          } catch {
            return false;
          }
        }
        return r.status === 503; // Service unavailable is valid under stress
      }
    };

    const passed = check(res, checks);
    
    if (!passed) {
      console.log(`⚠️  VU ${vu_id}: Request failed - Status: ${res.status}, Duration: ${duration}ms`);
    } else if (res.status === 200) {
      const body = JSON.parse(res.body);
      console.log(`✅ VU ${vu_id}: Success - Job ${body.job_id.substring(0,8)}..., Duration: ${duration}ms`);
    } else if (res.status === 503) {
      console.log(`🔄 VU ${vu_id}: System busy (503), Duration: ${duration}ms`);
    }
  });

  // Variable think time based on system load
  const think_time = Math.random() * 3 + 1; // 1-4 seconds
  sleep(think_time);
}

export function teardown(data) {
  const total_duration = (Date.now() - data.start_time) / 1000;
  console.log(`🏁 Stress test completed in ${total_duration.toFixed(1)} seconds`);
  
  // Final system status
  const final_status = http.get(`${BASE_URL}/system/status`);
  if (final_status.status === 200) {
    const status = JSON.parse(final_status.body);
    console.log(`📊 Final system state:`);
    console.log(`   Active jobs: ${status.active_jobs || 0}`);
    console.log(`   CPU: ${(status.performance?.cpu_percent || 0).toFixed(1)}%`);
    console.log(`   Memory: ${(status.performance?.memory_percent || 0).toFixed(1)}%`);
  }
  
  // Export test results
  console.log(`📈 Test metrics available in k6 output`);
}