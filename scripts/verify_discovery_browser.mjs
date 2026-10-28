import { createRequire } from "node:module";
import path from "node:path";
const [url, apw, output] = process.argv.slice(2);
const { chromium, expect: baseExpect } = createRequire(path.join(apw, "package.json"))("@playwright/test");
const expect = baseExpect.configure({ timeout: 20000 });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  await page.goto(url);
  await page.getByText("Discover and add papers", { exact: true }).first().click();
  const discovery = page.getByRole("region", { name: "Discover and add papers", exact: true });
  await discovery.getByLabel("Discovery provider").selectOption("crossref");
  await discovery.getByLabel("Discovery query or identifier").fill("conditions");
  await discovery.getByRole("button", { name: "Find candidate papers", exact: true }).click();
  await expect(discovery.getByRole("heading", { name: "Literal conditions: no effect at 5 mg" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Project papers" }).getByRole("link")).toHaveCount(1);
  // Lose only the first mutation response after it reaches the real backend.
  let lose = true;
  const ids = [];
  await page.route("**/api/workflow", async (route) => {
    if (route.request().method() === "POST" && route.request().postDataJSON().action === "discovery_select") {
      ids.push(route.request().postDataJSON().request_id);
      if (lose) {
        lose = false;
        await route.fetch();
        await route.abort("failed");
        return;
      }
    }
    await route.continue();
  });
  await discovery.getByRole("button", { name: "Add selected PDF", exact: true }).click();
  await expect(discovery.getByRole("alert")).toBeVisible();
  await discovery.getByRole("button", { name: "Add selected PDF", exact: true }).click();
  await expect(discovery.getByRole("status")).toContainText("p2: PDF added");
  expect(ids[0]).toBe(ids[1]);
  await expect(page.getByRole("navigation", { name: "Project papers" }).getByRole("link")).toHaveCount(2);
  await discovery.getByRole("button", { name: "Keep reference without PDF", exact: true }).click();
  await expect(discovery.getByRole("status")).toContainText("No PDF source reported");
  await expect(page.getByRole("navigation", { name: "Project papers" }).getByRole("link")).toHaveCount(2);
  await discovery.getByRole("heading", { name: "Literal conditions: no effect at 5 mg" }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(output, "discovery-desktop.png"), fullPage: true });
  const selected = page.getByRole("navigation", { name: "Project papers" }).getByRole("link", { name: /Literal conditions: no effect at 5 mg/ });
  await page.getByRole("tab", { name: "Notes", exact: true }).click();
  const beforeSwitch = await page.locator(".reader-toolbar").boundingBox();
  await page.evaluate(() => { window.readerSwitchProbe = "same document"; });
  await selected.click();
  await expect(page.locator("#textLayer span").first()).toHaveText("Selected discovery source.");
  expect(await page.evaluate(() => window.readerSwitchProbe)).toBe("same document");
  expect(await page.locator(".reader-toolbar").boundingBox()).toEqual(beforeSwitch);
  await expect(page.getByRole("tab", { name: "Notes", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#toggleControlsBtn").click();
  await page.getByText("Discover and add papers", { exact: true }).first().click();
  await discovery.getByLabel("Saved discovery").selectOption({ index: 1 });
  await expect(discovery.getByRole("heading", { name: "Literal conditions: no effect at 5 mg" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  await discovery.getByRole("heading", { name: "Literal conditions: no effect at 5 mg" }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(output, "discovery-mobile.png"), fullPage: true });
  expect(errors).toEqual([]);
  console.log("Discovery browser journey passed.");
} catch (error) {
  if (process.env.GITHUB_ACTIONS === "true") {
    const message = String(error.stack ?? error).slice(-6000).replaceAll("%", "%25").replaceAll("\r", "%0D").replaceAll("\n", "%0A");
    console.log(`::error title=Discovery browser failure::${message}`);
  }
  throw error;
} finally {
  await browser.close();
}
