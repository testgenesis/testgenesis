
import { test, expect } from '@playwright/test';

test('login_success_flow_8323', async ({ page }) => {
    await page.goto('/');
    await page.goto('/login');
    await page.fill('login_form [name="timestamp"]', '2025-08-16T23:45:27.355239');
    await page.click('login_form');
    await page.click('login_button');
    await page.goto('/dashboard');
});
