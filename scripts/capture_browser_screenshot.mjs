import { chromium, devices } from "playwright";

async function main() {
  const url = process.argv[2];
  const output = process.argv[3];
  const view = process.argv[4] || "gpu-focus";
  const selector = process.argv[5] || "";

  if (!url || !output) {
    throw new Error("Usage: node capture_browser_screenshot.mjs <url> <output>");
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    ...devices["Desktop Chrome"],
    viewport: { width: 1600, height: 1100 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForFunction(() => {
    const status = document.getElementById("status")?.textContent || "";
    const gpuUtil = document.getElementById("gpuUtil")?.textContent || "";
    return !status.includes("Connecting") && gpuUtil !== "n/a" && gpuUtil !== "";
  }, { timeout: 15000 });

  if (view && view !== "gpu-focus") {
    await page.click(`[data-view="${view}"]`);
  }

  await page.waitForTimeout(8000);

  if (selector) {
    await page.locator(selector).screenshot({ path: output });
  } else {
    await page.screenshot({ path: output, fullPage: false });
  }

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
