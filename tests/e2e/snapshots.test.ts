import { expect, Locator, Page, test } from "@playwright/test";

import { VIEWPORT_WIDTH } from "../playwright.config";

// Playwright test runner provides `process.env`, but this folder doesn't have Node typings.
declare const process: any;

const BASE_URL = "http://127.0.0.1:5000";
const FAVA_URL = `${BASE_URL}/beancount`;

// Fava native pages
const favaPages = [
  { name: "Balance Sheet", url: `${FAVA_URL}/balance_sheet/` },
  { name: "Income Statement", url: `${FAVA_URL}/income_statement/` },
  { name: "Trial Balance", url: `${FAVA_URL}/trial_balance/` },
  // { name: "Journal", url: `${FAVA_URL}/journal/` },
];

// FavaDashboards extension pages
const DASHBOARDS_URL = `${FAVA_URL}/extension/FavaDashboards/`;

type DashboardPageSpec = {
  name: string;
  url: string;
  clip?: { x: number; y: number; width: number; height: number };
  /** Locator function: screenshot just this element instead of the full page. */
  locator?: (page: Page) => Locator;
  /** Optional setup to run after page load but before screenshot. */
  setup?: (page: Page) => Promise<void>;
};

const dashboardPages: DashboardPageSpec[] = [
  {
    name: "Overview",
    url: `${DASHBOARDS_URL}`,
    setup: async (page) => {
      await page.getByPlaceholder("Time").fill("2024-01 to 2024-06");
      await page.getByPlaceholder("Time").press("Enter");
      await page.waitForLoadState("networkidle");
    },
  },
  { name: "Assets", url: `${DASHBOARDS_URL}?dashboard=assets` },
  {
    name: "Net Worth",
    url: `${DASHBOARDS_URL}?dashboard=accounts`,
    clip: { x: 0, y: 0, width: VIEWPORT_WIDTH, height: 1024 },
    setup: async (page) => {
      await page.getByPlaceholder("Time").fill("2024-01 to 2024-06");
      await page.getByPlaceholder("Time").press("Enter");
      await page.waitForLoadState("networkidle");
    },
  },
  {
    name: "Income and Expenses",
    url: `${DASHBOARDS_URL}?dashboard=income-and-expenses`,
    clip: { x: 0, y: 0, width: VIEWPORT_WIDTH, height: 1024 },
  },
  {
    name: "Expenses Detailed",
    url: `${DASHBOARDS_URL}?dashboard=expenses-detailed`,
    clip: { x: 0, y: 0, width: VIEWPORT_WIDTH, height: 1024 },
  },
  {
    name: "Expenses Heatmap",
    url: `${DASHBOARDS_URL}?dashboard=expenses-detailed`,
    setup: async (page) => {
      await page
        .getByRole("heading", { name: "Expenses Calendar Heatmap" })
        .scrollIntoViewIfNeeded();
    },
  },
  { 
    name: "Locations", url: `${DASHBOARDS_URL}?dashboard=travelling`,
    clip: { x: 0, y: 0, width: VIEWPORT_WIDTH, height: 1024 },
  },
  { name: "Sankey", url: `${DASHBOARDS_URL}?dashboard=sankey` },
];

type ExtensionPageSpec = {
  name: string;
  url: string;
  setup?: (page: Page) => Promise<void>;
};

// Other bundled extensions
const extensionPages: ExtensionPageSpec[] = [
  {
    name: "Portfolio Returns",
    url: `${FAVA_URL}/extension/FavaPortfolioReturns/`,
    setup: async (page) => {
      await page.getByPlaceholder("Time").fill("2024");
      await page.getByPlaceholder("Time").press("Enter");
      await page.waitForLoadState("networkidle");
    },
  },
  {
    name: "Currency Tracker",
    url: `${FAVA_URL}/extension/FavaCurrencyTracker/`,
    setup: async (page) => {
      await page.getByRole("combobox", { name: "Currency" }).pressSequentially("USD");
      await page.getByRole("option", { name: "USD", exact: true }).click();
      await page.getByPlaceholder("Time").fill("2024");
      await page.getByPlaceholder("Time").press("Enter");
      await page.waitForLoadState("networkidle");
    },
  },
  { name: "Fava Git", url: `${FAVA_URL}/extension/FavaGit/` },
  { name: "Beantab", url: `${FAVA_URL}/extension/BeanTab/?accountFilter=%5B%22Assets%3A.*%22%5D&groupByAccount=false&hideAccountsWithNoEntries=true` },
  { name: "Beantab with deltas", url: `${FAVA_URL}/extension/BeanTab/?accountFilter=%5B%22Assets%3A.*%22%5D&groupByAccount=false&hideAccountsWithNoEntries=true&showDeltas=true` },
];

async function expectScreenshot(
  page: Page,
  opts?: {
    clip?: { x: number; y: number; width: number; height: number };
    locator?: Locator;
    setup?: (page: Page) => Promise<void>;
  },
) {
  await page.evaluate(() => {
    document.body.style.height = "inherit";
  });
  await page.waitForLoadState("networkidle");
  if (opts?.setup) {
    await opts.setup(page);
  }
  await expect(page.locator(".MuiCircularProgress-root")).toHaveCount(0, {
    timeout: 15000,
  });
  await expect(page.locator(".MuiSkeleton-root")).toHaveCount(0, {
    timeout: 15000,
  });
  // Let ECharts animations and Fava JS settle
  await page.waitForTimeout(2000);

  const snapshotOpts = { timeout: 15000, maxDiffPixelRatio: 0.005 };

  if (opts?.locator) {
    await expect(opts.locator).toHaveScreenshot(snapshotOpts);
  } else {
    const screenshotOptions = opts?.clip
      ? ({ fullPage: false, clip: opts.clip } as const)
      : ({ fullPage: true } as const);
    await expect(page).toHaveScreenshot({ ...screenshotOptions, ...snapshotOpts });
  }
}

// --- PNG Snapshot Tests ---

test.describe("PNG Snapshot Tests", () => {
  test.skip(!process.env.CONTAINER, "snapshot tests must run in a container");

  test.describe("Light Theme", () => {
    test.describe("Fava Pages", () => {
      favaPages.forEach(({ name, url }) => {
        test(name, async ({ page }) => {
          await page.goto(url);
          await expectScreenshot(page);
        });
      });
    });

    test.describe("Dashboards", () => {
      dashboardPages.forEach(({ name, url, clip, locator, setup }) => {
        test(name, async ({ page }) => {
          await page.goto(url);
          await expectScreenshot(page, { clip, locator: locator?.(page), setup });
        });
      });
    });

    test.describe("Extensions", () => {
      extensionPages.forEach(({ name, url, setup }) => {
        test(name, async ({ page }) => {
          await page.goto(url);
          await expectScreenshot(page, { setup });
        });
      });
    });
  });

  test.describe("Dark Theme", () => {
    test.use({ colorScheme: "dark" });

    test.describe("Fava Pages", () => {
      favaPages.forEach(({ name, url }) => {
        test(name, async ({ page }) => {
          await page.goto(url);
          await expectScreenshot(page);
        });
      });
    });

    test.describe("Dashboards", () => {
      dashboardPages.forEach(({ name, url, clip, locator, setup }) => {
        test(name, async ({ page }) => {
          await page.goto(url);
          await expectScreenshot(page, { clip, locator: locator?.(page), setup });
        });
      });
    });

    test.describe("Extensions", () => {
      extensionPages.forEach(({ name, url, setup }) => {
        test(name, async ({ page }) => {
          await page.goto(url);
          await expectScreenshot(page, { setup });
        });
      });
    });
  });
});

// --- HTML/ARIA Snapshot Tests ---

test.describe("HTML Snapshot Tests", () => {
  test.skip(!process.env.CONTAINER, "snapshot tests must run in a container");

  test.describe("Fava Pages", () => {
    favaPages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(url);
        await expect(page.locator("body")).toMatchAriaSnapshot();
      });
    });
  });

  test.describe("Dashboards", () => {
    dashboardPages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(url);
        await expect(page.locator("body")).toMatchAriaSnapshot();
      });
    });
  });

  test.describe("Extensions", () => {
    extensionPages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(url);
        await expect(page.locator("body")).toMatchAriaSnapshot();
      });
    });
  });
});
