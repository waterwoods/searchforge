#!/usr/bin/env node
/**
 * Entry Unification E2E Test
 * ===========================
 * Tests frontend-backend integration through Vite proxy
 * 
 * Prerequisites:
 *   - Backend running on port 8011
 *   - Frontend dev server running on port 3000
 * 
 * Exit codes:
 *   0 - All tests pass
 *   1 - Tests failed
 */

import fetch from 'node-fetch'
import fs from 'fs/promises'
import path from 'path'

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000'
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8011'
const TIMEOUT = 10000

let testsPassed = 0
let testsFailed = 0

// Results collector
const results = []

function logTest(status, message) {
    const symbol = status === 'PASS' ? '✓' : status === 'FAIL' ? '✗' : 'ℹ'
    const line = `${symbol} ${message}`
    console.log(line)
    results.push(line)

    if (status === 'PASS') testsPassed++
    if (status === 'FAIL') testsFailed++
}

function logHeader(message) {
    console.log('')
    console.log('='.repeat(50))
    console.log(message)
    console.log('='.repeat(50))
    results.push('')
    results.push(message)
}

async function testBackendDirect() {
    logHeader('Test 1: Backend Direct Access')

    try {
        const response = await fetch(`${BACKEND_URL}/api/agent/summary?v=2`, { timeout: TIMEOUT })

        if (response.ok) {
            const data = await response.json()
            if (data.ok !== undefined) {
                logTest('PASS', `Backend /api/agent/summary?v=2 returns valid JSON`)
            } else {
                logTest('FAIL', `Backend returned JSON but missing 'ok' field`)
            }
        } else {
            logTest('FAIL', `Backend returned status ${response.status}`)
        }
    } catch (error) {
        logTest('FAIL', `Backend request failed: ${error.message}`)
    }
}

async function testFrontendProxy() {
    logHeader('Test 2: Frontend Proxy Access')

    try {
        const response = await fetch(`${FRONTEND_URL}/api/agent/summary?v=2`, { timeout: TIMEOUT })

        if (response.ok) {
            const data = await response.json()
            if (data.ok !== undefined) {
                logTest('PASS', `Frontend proxy /api/agent/summary?v=2 OK`)

                // Check if data looks reasonable
                if ('delta_p95_pct' in data && 'delta_qps_pct' in data) {
                    logTest('PASS', `Response contains expected metrics`)
                } else {
                    logTest('FAIL', `Response missing expected fields`)
                }
            } else {
                logTest('FAIL', `Frontend proxy returned JSON but missing 'ok' field`)
            }
        } else {
            logTest('FAIL', `Frontend proxy returned status ${response.status}`)
        }
    } catch (error) {
        logTest('FAIL', `Frontend proxy request failed: ${error.message}`)
    }
}

async function testHealthEndpoint() {
    logHeader('Test 3: Health Endpoints')

    try {
        // Test /readyz through frontend proxy
        const response = await fetch(`${FRONTEND_URL}/readyz`, { timeout: TIMEOUT })

        if (response.ok) {
            const data = await response.json()
            if (data.ok === true) {
                logTest('PASS', `/readyz accessible via frontend`)
            } else {
                logTest('WARN', `/readyz returns data but ok=${data.ok}`)
            }
        } else {
            logTest('FAIL', `/readyz returned status ${response.status}`)
        }
    } catch (error) {
        logTest('FAIL', `/readyz request failed: ${error.message}`)
    }
}

async function testCORS() {
    logHeader('Test 4: CORS Check')

    try {
        const response = await fetch(`${FRONTEND_URL}/api/agent/summary?v=2`, {
            method: 'GET',
            timeout: TIMEOUT
        })

        // Check CORS headers (in Node.js fetch, these are not exposed the same way as browser)
        // But we can check if request succeeds without CORS error
        if (response.ok) {
            logTest('PASS', `No CORS errors (request successful)`)
        } else {
            logTest('WARN', `Request returned ${response.status}, may have CORS issues`)
        }
    } catch (error) {
        if (error.message.includes('CORS')) {
            logTest('FAIL', `CORS error detected: ${error.message}`)
        } else {
            logTest('INFO', `Request failed but not due to CORS: ${error.message}`)
        }
    }
}

async function generateReport() {
    logHeader('Generating Report')

    const reportDir = 'reports'
    const reportFile = path.join(reportDir, 'ENTRY_E2E_RESULT.txt')

    // Ensure reports directory exists
    try {
        await fs.mkdir(reportDir, { recursive: true })
    } catch (err) {
        // Directory may already exist
    }

    const reportContent = `
=================================================================
Entry Unification E2E Test Result
=================================================================
Date: ${new Date().toISOString()}
Frontend: ${FRONTEND_URL}
Backend: ${BACKEND_URL}

-----------------------------------------------------------------
Results
-----------------------------------------------------------------
✅ Tests passed: ${testsPassed}
❌ Tests failed: ${testsFailed}

${results.join('\n')}

-----------------------------------------------------------------
Status
-----------------------------------------------------------------
${testsFailed === 0 ? '✅ ALL E2E TESTS PASSED' : '❌ SOME TESTS FAILED'}

${testsFailed === 0 ? `
Frontend can successfully access backend through Vite proxy.
No CORS issues detected.
Entry unification is working correctly.
` : `
Some tests failed. Check errors above.
Ensure both backend and frontend are running:
  - Backend: uvicorn app_main:app --port 8011
  - Frontend: npm run dev (in frontend/)
`}
=================================================================
`.trim()

    await fs.writeFile(reportFile, reportContent, 'utf-8')
    logTest('INFO', `Report saved to ${reportFile}`)
}

function printSummary() {
    console.log('')
    console.log('='.repeat(50))
    console.log('Summary')
    console.log('='.repeat(50))
    console.log(`Tests passed: ${testsPassed}`)
    console.log(`Tests failed: ${testsFailed}`)
    console.log('')

    if (testsFailed === 0) {
        console.log('✅ ALL E2E TESTS PASSED')
        console.log('')
        console.log('Frontend proxy → Backend integration working!')
        return 0
    } else {
        console.log('❌ SOME TESTS FAILED')
        console.log('')
        console.log('Please ensure:')
        console.log('  1. Backend is running: uvicorn app_main:app --port 8011')
        console.log('  2. Frontend is running: npm run dev')
        return 1
    }
}

async function main() {
    console.log('Entry Unification E2E Test')
    console.log(`Frontend: ${FRONTEND_URL}`)
    console.log(`Backend: ${BACKEND_URL}`)

    await testBackendDirect()
    await testFrontendProxy()
    await testHealthEndpoint()
    await testCORS()
    await generateReport()

    const exitCode = printSummary()
    process.exit(exitCode)
}

main()

