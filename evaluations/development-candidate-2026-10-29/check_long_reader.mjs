// Installed-candidate engineering check. It measures rasters, not scientific validity.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';

const report = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(report, '../../../.development-candidate/2026-10-29-c1');
const output = path.join(root, 'long-reader');
fs.mkdirSync(output);
const python = path.join(root, 'installed/Scripts/python.exe');
const executable = path.join(root, 'installed/Scripts/sci.exe');
const workspace = path.join(output, 'project');
const cli = (...args) => JSON.parse(execFileSync(executable, [...args, '--workspace', workspace, '--json'], {encoding:'utf8', timeout:90000}));
const {chromium, expect} = createRequire(path.join(root, 'source/agent-pdf-workbench/package.json'))('@playwright/test');
function pdf(pages, label) {
  const objects = ['<< /Type /Catalog /Pages 2 0 R >>', `<< /Type /Pages /Kids [${Array.from({length:pages},(_,i)=>`${4+i*2} 0 R`).join(' ')}] /Count ${pages} >>`, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'];
  for (let i=0;i<pages;i++) {
    const text=`BT /F1 18 Tf 72 720 Td (${label} page ${i+1} source passage.) Tj ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents ${5+i*2} 0 R >>`, `<< /Length ${text.length} >>\nstream\n${text}\nendstream`);
  }
  let content='%PDF-1.4\n'; const offsets=[0];
  objects.forEach((object,i)=>{offsets.push(Buffer.byteLength(content));content+=`${i+1} 0 obj\n${object}\nendobj\n`;});
  const xref=Buffer.byteLength(content);
  content+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`;
  for(const offset of offsets.slice(1)) content+=`${String(offset).padStart(10,'0')} 00000 n \n`;
  return content+`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
}
const first=path.join(output,'thirty-pages.pdf'), second=path.join(output,'one-page.pdf');
fs.writeFileSync(first,pdf(30,'Long document')); fs.writeFileSync(second,pdf(1,'Second document'));
const samples=[], errors=[]; let browser, failure;
try {
  const opened=cli('start',first,'--question','Continuous reader acceptance fixture','--no-open');
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror', error=>errors.push(String(error)));
  await page.goto(opened.viewer_url);
  await expect(page.locator('.pdf-document-container')).toHaveCount(30);
  await page.locator('#fitWidthBtn').click();
  for(const number of [1,5,10,15,20,25,30,1]) {
    const target=page.locator(`.pdf-document-container[data-page="${number}"]`);
    await target.evaluate(element=>element.scrollIntoView({block:'start'}));
    await expect(target).toHaveAttribute('aria-busy','false');
    await expect(target.locator('.text-layer')).toContainText(`page ${number} source passage`);
    // Wait for both renderer workers and the scroll report to settle.
    await page.waitForFunction(() => ![...document.querySelectorAll('.pdf-document-container')].some(e=>e.querySelector('canvas').width>0 && e.getAttribute('aria-busy')==='true'));
    const sample=await page.evaluate(()=>{
      const canvases=[...document.querySelectorAll('.pdf-document-container canvas')];
      const active=canvases.filter(c=>c.width>0&&c.height>0);
      return {placeholders:canvases.length,active:active.length,pixel_bytes:active.reduce((n,c)=>n+c.width*c.height*4,0),pages:active.map(c=>Number(c.parentElement.dataset.page)),zoom:document.querySelector('#zoomInfo').textContent,js_heap:performance.memory?.usedJSHeapSize??null};
    });
    samples.push({requested_page:number,...sample});
    assert.ok(sample.active<=7,JSON.stringify(sample));
  }
  await page.screenshot({path:path.join(output,'thirty-pages.png')});
  const added=cli('add',second);
  const resumed=cli('resume','--paper','p2','--no-open');
  await page.goto(resumed.viewer_url);
  await expect(page.locator('.pdf-document-container')).toHaveCount(1);
  await expect(page.locator('.text-layer')).toContainText('Second document page 1');
  assert.equal(await page.locator('.text-layer').filter({hasText:'Long document'}).count(),0);
  assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(output,'second-paper.png')});
} catch(error) {failure=String(error.stack??error);}
finally {
  if(browser) await browser.close();
  try { cli('stop'); } catch(error) { failure??=String(error); }
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({candidate:'2026-10-29-c1',protocol:'protocol-v2.json',passed:!failure,scope:'fit-width scrolling and paper switch only; 100% zoom, annotation and search gates remain open',samples,errors,failure},null,2));
}
if(failure) throw new Error(failure);
console.log(JSON.stringify({passed:true,max_active_rasters:Math.max(...samples.map(s=>s.active)),max_pixel_bytes:Math.max(...samples.map(s=>s.pixel_bytes))}));
