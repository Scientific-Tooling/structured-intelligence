// Exercise the actual installed CLI and reader, including user-created evidence.
// Usage: node scripts/verify_workflow_browser.mjs PYTHON APW_DIRECTORY [OUTPUT_DIRECTORY]
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";

const [python, apw, output] = process.argv.slice(2);
if (!python || !apw) throw new Error("Supply the installed Python and APW checkout paths");
const artifacts = output ? path.resolve(output) : fs.mkdtempSync(path.join(os.tmpdir(), "workflow-browser-"));
fs.mkdirSync(artifacts, { recursive: true });
const workspace = path.join(artifacts, "review α");
const pdf = path.join(artifacts, "input paper.pdf");
const stream = "BT /F1 18 Tf 72 720 Td (Reading workflow test source.) Tj ET";
const objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
  "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
  "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`];
let content = "%PDF-1.4\n";
const offsets = [0];
for (const [index, object] of objects.entries()) {
  offsets.push(Buffer.byteLength(content));
  content += `${index + 1} 0 obj\n${object}\nendobj\n`;
}
const xref = Buffer.byteLength(content);
content += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
for (const offset of offsets.slice(1)) content += `${String(offset).padStart(10, "0")} 00000 n \n`;
content += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
fs.writeFileSync(pdf, content);
const executable = execFileSync(python, ["-c",
  "import os, pathlib, sysconfig; print(pathlib.Path(sysconfig.get_path('scripts')) / ('sci.exe' if os.name == 'nt' else 'sci'))"],
  { encoding: "utf8", timeout: 10000 }).trim();
const cli = (...args) => JSON.parse(execFileSync(executable,
  [...args, "--workspace", workspace, "--json"],
  { encoding: "utf8", timeout: 60000 }));
const { chromium, expect: baseExpect } = createRequire(path.join(path.resolve(apw), "package.json"))("@playwright/test");
const expect = baseExpect.configure({ timeout: 20000 });
let browser;
const errors = [];
try {
  const opened = cli("start", pdf, "--question", "What does this source record?", "--no-open");
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.on("pageerror", error => errors.push(String(error)));
  await page.goto(opened.viewer_url);
  await expect(page.locator("#textLayer span").first()).toBeVisible();
  await expect(page.getByRole("tab", { name: /^Evidence/ })).toBeVisible();
  await page.getByText("Highlight tools & comments", {exact: true}).click();
  await page.locator("#annotationCommentInput").fill("Unreviewed observation from the test source.");
  await page.evaluate(() => {
    const span = document.querySelector("#textLayer span");
    const range = document.createRange();
    range.selectNodeContents(span);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  });
  await page.locator("#highlightBtn").click();
  const panel = page.locator(".panel.workspace");
  await expect(panel.getByRole("checkbox")).toHaveCount(1);
  await panel.getByRole("checkbox").check();
  await panel.getByRole("button", { name: "Preview selected evidence", exact: true }).click();
  await expect(panel.getByRole("region", { name: "Import preview" })).toContainText("Reading workflow test source.");
  await page.screenshot({ path: path.join(artifacts, "desktop-preview.png"), fullPage: true });
  await panel.getByRole("button", { name: "Import evidence & create brief", exact: true }).click();
  await expect(panel.getByRole("button", {name: "View project brief →", exact: true})).toBeVisible();
  await panel.getByRole("tab", {name: "Brief", exact: true}).click();
  await expect(panel.getByRole("button", { name: "Download brief", exact: true })).toBeVisible();
  const downloadEvent = page.waitForEvent("download");
  await panel.getByRole("button", { name: "Download brief", exact: true }).click();
  const download = await downloadEvent;
  await download.saveAs(path.join(artifacts, "downloaded-brief.md"));
  const brief = fs.readFileSync(path.join(artifacts, "downloaded-brief.md"), "utf8");
  expect(brief).toContain("Reading workflow test source.");
  expect(brief).toContain("Unreviewed reading material");
  const link = panel.getByRole("link", { name: "Open supporting passage 1", exact: true });
  const citation = await link.getAttribute("href");
  await link.click();
  await expect(page.locator("#textLayer span").first()).toBeVisible();
  await expect(page.locator("#annotationList .selected")).toContainText("Reading workflow test source.");
  await page.screenshot({ path: path.join(artifacts, "desktop-brief.png"), fullPage: true });
  cli("stop");
  const resumed = cli("resume", "--no-open");
  expect(resumed.session_id).toBe(opened.session_id);
  expect(resumed.viewer_url).toBe(opened.viewer_url);
  await page.goto(citation);
  await expect(page.locator("#annotationList .selected")).toContainText("Reading workflow test source.");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#toggleWorkspaceBtn").click();
  await expect(panel.getByRole("tab", { name: /^Evidence/ })).toBeVisible();
  await panel.getByRole("tab", {name: "Brief", exact: true}).click();
  await expect(panel.getByRole("button", { name: "Download brief", exact: true })).toBeVisible();
  await page.screenshot({ path: path.join(artifacts, "mobile-brief.png"), fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  // Grow an existing project while the first paper's tab remains open.
  const secondPdf = path.join(artifacts, "second paper.pdf");
  fs.writeFileSync(secondPdf, content.replace("Reading workflow test source.", "Another workflow test source."));
  const added = cli("add", secondPdf);
  expect(added.added).toEqual(["p2"]);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload();
  const navigation = page.getByRole("navigation", { name: "Project papers" });
  await expect(navigation.getByRole("link")).toHaveCount(2);
  const secondUrl = await navigation.getByRole("link", { name: /p2.*second paper/ }).getAttribute("href");
  const secondTab = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  secondTab.on("pageerror", error => errors.push(String(error)));
  await secondTab.goto(secondUrl);
  await expect(secondTab.locator("#textLayer span").first()).toHaveText("Another workflow test source.");
  await secondTab.getByText("Highlight tools & comments", {exact: true}).click();
  await secondTab.locator("#annotationCommentInput").fill("An observation from the second paper.");
  await secondTab.evaluate(() => {
    const range = document.createRange();
    range.selectNodeContents(document.querySelector("#textLayer span"));
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  });
  await secondTab.locator("#highlightBtn").click();
  const secondPanel = secondTab.locator(".panel.workspace");
  await expect(secondPanel.getByRole("checkbox")).toHaveCount(1);
  await secondPanel.getByRole("checkbox").check();
  await secondPanel.getByRole("button", { name: "Preview selected evidence", exact: true }).click();
  await expect(secondPanel.getByRole("region", { name: "Import preview" })).toContainText("Another workflow test source.");
  await expect(panel.getByRole("region", { name: "Import preview" })).toContainText("Reading workflow test source.");
  await secondPanel.getByRole("button", { name: "Import evidence & create brief", exact: true }).click();
  await expect(secondPanel.getByRole("button", {name: "View project brief →", exact: true})).toBeVisible();
  await secondPanel.getByRole("tab", {name: "Brief", exact: true}).click();
  await expect(secondPanel.getByRole("button", { name: "Download brief", exact: true })).toBeVisible();
  const project = cli("status", "--paper", "p2");
  expect(project.brief.counts.evidence).toBe(2);
  expect(project.brief.counts.unreviewed).toBe(2);
  expect(project.brief.text).toContain("## Coverage");
  await secondTab.screenshot({ path: path.join(artifacts, "project-desktop.png"), fullPage: true });
  await secondTab.setViewportSize({ width: 390, height: 844 });
  await secondTab.locator("#toggleWorkspaceBtn").click();
  await expect(secondPanel.getByRole("tab", {name: "Brief", exact: true})).toBeVisible();
  await secondTab.locator("#toggleControlsBtn").click();
  await expect(secondTab.getByRole("navigation", { name: "Project papers" })).toBeVisible();
  await expect(secondPanel).toBeHidden();
  await secondTab.locator("#toggleWorkspaceBtn").click();
  await expect(secondTab.getByRole("navigation", { name: "Project papers" })).toBeHidden();
  expect(await secondTab.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  await secondTab.screenshot({ path: path.join(artifacts, "project-mobile.png"), fullPage: true });
  cli("stop");
  cli("resume", "--no-open");
  await secondTab.setViewportSize({ width: 1440, height: 1000 });
  for (const url of project.brief.passage_urls) {
    await secondTab.goto(url);
    await expect(secondTab.locator("#annotationList .selected")).toBeVisible();
    await expect(secondTab.locator("#textLayer span").first()).toBeVisible();
  }
  fs.writeFileSync(path.join(artifacts, "project-brief.md"), project.brief.text);
  expect(errors).toEqual([]);
  fs.writeFileSync(path.join(artifacts, "receipt.json"), JSON.stringify({
    passed: true, user_created_highlight: true, preview_and_apply: true, download: true,
    passage_link: true, stop_and_resume: true, desktop_and_mobile: true, page_errors: errors,
    multiple_papers: true, separate_tabs: true, project_citations_after_resume: true,
    workspace, brief: project.brief.path,
  }, null, 2));
  console.log(`Browser journey passed. Artifacts: ${artifacts}`);
} finally {
  if (browser) await browser.close();
  if (fs.existsSync(path.join(workspace, "workspace.json"))) cli("stop");
}
