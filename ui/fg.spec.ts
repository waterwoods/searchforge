import { test, expect } from '@playwright/test';

test('FlowGraph Self-Test', async ({ page }) => {
    // Navigate to the self-test page
    await page.goto('/fg-selftest');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Click the "Run Self-Test" button
    await page.click('button:has-text("Run Self-Test")');

    // Wait for the test to complete (look for the result alert)
    await page.waitForSelector('.ant-alert', { timeout: 10000 });

    // Get the test result text
    const resultAlert = page.locator('.ant-alert');
    const resultText = await resultAlert.textContent();

    // Check if the test passed
    expect(resultText).toContain('SELFTEST PASS');

    // Also check that we don't see any failure messages
    const failAlert = page.locator('.ant-alert-error');
    const failCount = await failAlert.count();
    expect(failCount).toBe(0);
});

test('FlowGraph Self-Test - Check Console Logs', async ({ page }) => {
    const consoleLogs: string[] = [];

    // Capture console logs
    page.on('console', msg => {
        consoleLogs.push(`${msg.type()}: ${msg.text()}`);
    });

    // Navigate to the self-test page
    await page.goto('/fg-selftest');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Click the "Run Self-Test" button
    await page.click('button:has-text("Run Self-Test")');

    // Wait for the test to complete
    await page.waitForSelector('.ant-alert', { timeout: 10000 });

    // Check that we don't see duplicate render warnings
    const duplicateRenderLogs = consoleLogs.filter(log =>
        log.includes('[FG] duplicate render') || log.includes('duplicate-render')
    );

    expect(duplicateRenderLogs.length).toBe(0);

    // Check that we don't see phase violations
    const phaseViolationLogs = consoleLogs.filter(log =>
        log.includes('PHASE VIOLATION')
    );

    expect(phaseViolationLogs.length).toBe(0);

    // Log all console messages for debugging
    console.log('Console logs captured:', consoleLogs);
});
