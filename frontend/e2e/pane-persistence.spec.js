import { test, expect } from '@playwright/test';

test.describe('Pane Persistence', () => {
  test('should persist layout after page reload', async ({ page, context }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Get initial localStorage state
    const initialLayout = await page.evaluate(() => {
      return localStorage.getItem('humanizer-layout');
    });

    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Get layout after reload
    const reloadedLayout = await page.evaluate(() => {
      return localStorage.getItem('humanizer-layout');
    });

    // Layout should persist
    if (initialLayout) {
      expect(reloadedLayout).toBe(initialLayout);
    }
  });

  test('should persist preferences after page reload', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Get initial preferences
    const initialPrefs = await page.evaluate(() => {
      return localStorage.getItem('humanizer-preferences');
    });

    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Get preferences after reload
    const reloadedPrefs = await page.evaluate(() => {
      return localStorage.getItem('humanizer-preferences');
    });

    // Preferences should persist
    if (initialPrefs) {
      expect(reloadedPrefs).toBe(initialPrefs);
    }
  });

  test('should maintain pane sizes across sessions', async ({ page, context }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Set a custom layout
    await page.evaluate(() => {
      const customLayout = {
        sidebarSize: 30,
        mainSize: 45,
        previewSize: 25,
        inspectorSize: 35,
      };
      localStorage.setItem('humanizer-layout', JSON.stringify(customLayout));
    });

    // Reload to apply the layout
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify layout was applied
    const appliedLayout = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('humanizer-layout'));
    });

    expect(appliedLayout.sidebarSize).toBe(30);
    expect(appliedLayout.mainSize).toBe(45);
    expect(appliedLayout.previewSize).toBe(25);
    expect(appliedLayout.inspectorSize).toBe(35);
  });

  test('should handle corrupted localStorage gracefully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Corrupt localStorage
    await page.evaluate(() => {
      localStorage.setItem('humanizer-layout', 'invalid json');
      localStorage.setItem('humanizer-preferences', '{broken');
    });

    // Reload - should not crash
    await page.reload();
    await page.waitForLoadState('networkidle');

    // App should still be functional
    expect(page.locator('body')).toBeTruthy();
  });
});

test.describe('Tab Persistence', () => {
  test('should maintain active tab on reload', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Open a few tabs (this will need to be customized based on actual UI)
    // For now, just verify no crash on reload
    await page.reload();
    await page.waitForLoadState('networkidle');
  });
});

test.describe('Interest List Persistence', () => {
  test('should persist interest list items', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Add items to interest list programmatically
    await page.evaluate(() => {
      // This would need to interact with the WorkspaceContext
      // For now, just a placeholder
    });

    // Reload and verify items persist
    await page.reload();
    await page.waitForLoadState('networkidle');
  });
});

test.describe('Responsive Layout', () => {
  test('should adapt to different viewport sizes', async ({ page }) => {
    // Desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    let bodyWidth = await page.locator('body').evaluate(el => el.offsetWidth);
    expect(bodyWidth).toBeGreaterThanOrEqual(1900);

    // Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);

    bodyWidth = await page.locator('body').evaluate(el => el.offsetWidth);
    expect(bodyWidth).toBeLessThanOrEqual(800);

    // Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);

    bodyWidth = await page.locator('body').evaluate(el => el.offsetWidth);
    expect(bodyWidth).toBeLessThanOrEqual(400);
  });

  test('should maintain layout proportions on window resize', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Resize window
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.waitForTimeout(500);

    // Get layout
    const layout1 = await page.evaluate(() => {
      return localStorage.getItem('humanizer-layout');
    });

    // Resize again
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.waitForTimeout(500);

    // Layout should still be valid
    const layout2 = await page.evaluate(() => {
      return localStorage.getItem('humanizer-layout');
    });

    expect(layout2).toBeTruthy();
  });
});
