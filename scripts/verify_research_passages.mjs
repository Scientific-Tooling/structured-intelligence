// Optional real-browser verification against the same viewer named in the briefs.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const [journeyPath, apwRoot, outputDirectory] = process.argv.slice(2);
if (!journeyPath || !apwRoot || !outputDirectory) {
  throw new Error("Usage: node verify_research_passages.mjs journey-results.json apw-checkout new-output-directory");
}
const journey = JSON.parse(fs.readFileSync(journeyPath, "utf8"));
if (journey.schema !== "scientific-tooling.scientific-journey-results.v1" || fs.existsSync(outputDirectory)) {
  throw new Error("Use a valid journey receipt and a new output directory");
}
const { chromium } = createRequire(path.resolve(apwRoot, "package.json"))("playwright");
fs.mkdirSync(outputDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });
const results = [];
const caseIds = new Set();
try {
  for (const source of journey.cases) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
    try {
      if (!/^[a-z0-9][a-z0-9-]{0,63}$/.test(source.case_id) || caseIds.has(source.case_id)) {
        throw new Error("Invalid or duplicate journey case ID");
      }
      caseIds.add(source.case_id);
      const page = await context.newPage();
      const url = new URL(source.url);
      if (!["http:", "https:"].includes(url.protocol) || !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)
          || url.searchParams.get("document_sha256") !== source.document_sha256) {
        throw new Error("Citation must identify the original PDF at a loopback viewer");
      }
      await page.goto(url.href, { waitUntil: "domcontentloaded" });
      await page.waitForFunction(() => {
        const status = document.querySelector("#statusText")?.textContent ?? "";
        return status.includes("passage ready") || /changed|missing|ambiguous|outside|failed/i.test(status);
      }, undefined, { timeout: 30000 });
      const status = await page.locator("#statusText").textContent();
      if (!status.includes("passage ready") || await page.locator("#pageJumpInput").inputValue() !== String(source.page)) {
        throw new Error(status || "Source passage did not render on the expected page");
      }
      await page.locator(".annotation-mark.selected").first().waitFor({ state: "visible" });
      await page.screenshot({ path: path.join(outputDirectory, `${source.case_id}.png`), fullPage: true });
      results.push({ case_id: source.case_id, document_sha256: source.document_sha256, page: source.page, passed: true });
    } catch (error) {
      results.push({ case_id: source.case_id, passed: false, error: String(error) });
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
const result = { schema: "scientific-tooling.source-browser-check.v1", corpus_revision: journey.corpus_revision,
  scientific_accuracy: null, cases: results, passed: results.every((source) => source.passed) };
fs.writeFileSync(path.join(outputDirectory, "browser-results.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
if (!result.passed) process.exitCode = 1;
