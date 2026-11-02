// Real installed reader checks. Each attempt preserves its own receipt and screenshots.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../..');
const [mode, outputArg, citationInput] = process.argv.slice(2);
assert.ok(['recovery', 'reader', 'citations', 'edges'].includes(mode));
const output = path.resolve(outputArg);
const python = process.env.ACCEPTANCE_PYTHON || path.join(root, '.development-candidate/2026-10-29-c1/installed/Scripts/python.exe');
const {chromium, expect: baseExpect} = createRequire(path.join(root, 'agent-pdf-workbench/package.json'))('@playwright/test');
const expect = baseExpect.configure({timeout: 20000});
// This preflight creates the directory and rejects any existing attempt.
execFileSync(python, [path.join(here, 'acceptance.py'), 'provenance', output], {encoding: 'utf8'});
fs.copyFileSync(fileURLToPath(import.meta.url),path.join(output,'browser.mjs'));
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const receipt = {mode, browser_harness_sha256: hash(fileURLToPath(import.meta.url)), checks: [], errors: [], passed: false};
const save = () => fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify(receipt, null, 2));
let workspace = path.join(output, 'project');
let browser, page;
const cli = (...args) => JSON.parse(execFileSync(python,
  ['-m', 'scientific_tooling', ...args.map(String), '--workspace', workspace, '--json'], {encoding:'utf8', timeout:120000}));
async function check(name, run) {
  const started = performance.now();
  try {
    const details = await run();
    receipt.checks.push({name, passed:true, seconds:(performance.now()-started)/1000, details});
  } catch(error) {
    receipt.checks.push({name, passed:false, seconds:(performance.now()-started)/1000, error:String(error.stack ?? error)});
    throw error;
  } finally {save();}
}
function pdf(pages, label, repeated = false) {
  const objects = ['<< /Type /Catalog /Pages 2 0 R >>', `<< /Type /Pages /Kids [${Array.from({length:pages},(_,i)=>`${4+i*2} 0 R`).join(' ')}] /Count ${pages} >>`, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'];
  for (let i=1;i<=pages;i++) {
    const text=`BT /F1 16 Tf 72 720 Td (${label} page ${String(i).padStart(2,'0')} source passage.) Tj 0 -40 Td (Shared search marker on every page.) Tj${repeated ? ' 0 -40 Td (Shared search marker on every page.) Tj' : ''} ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents ${5+i*2-2} 0 R >>`, `<< /Length ${text.length} >>\nstream\n${text}\nendstream`);
  }
  let content='%PDF-1.4\n'; const offsets=[0];
  objects.forEach((object,i)=>{offsets.push(Buffer.byteLength(content));content+=`${i+1} 0 obj\n${object}\nendobj\n`;});
  const xref=Buffer.byteLength(content);
  content+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`;
  for(const offset of offsets.slice(1)) content+=`${String(offset).padStart(10,'0')} 00000 n \n`;
  return content+`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
}
async function screenshot(name) {await page.screenshot({path:path.join(output, `${name}.png`), fullPage:true});}
async function ready(number, text) {
  const target=page.locator(`.pdf-document-container[data-page="${number}"]`);
  await expect(target).toHaveAttribute('aria-busy', 'false');
  if(text) await expect(target.locator('.text-layer')).toContainText(text);
  await expect(page.locator('#pageJumpInput')).toHaveValue(String(number));
  return target;
}
async function jump(number, text) {
  await page.locator('#pageJumpInput').fill(String(number));
  await page.locator('#pageJumpInput').press('Enter');
  return ready(number,text);
}
function editions() {
  const dir=path.join(workspace,'briefs');
  return Object.fromEntries(fs.readdirSync(dir).flatMap(id=>['record.json','brief.md'].map(name=>path.join(dir,id,name))
    .filter(p=>fs.existsSync(p)&&fs.statSync(p).isFile()).map(p=>[path.relative(dir,p),hash(p)])));
}
function unchanged(before) {const after=editions(); for(const [name,sha] of Object.entries(before)) assert.equal(after[name],sha,name);}
async function recovery() {
  const input=path.join(output,'source.pdf'); fs.writeFileSync(input,pdf(1,'Recovery'));
  const opened=cli('start',input,'--question','Browser failure acceptance fixture','--no-open');
  const annotation=cli('annotate','--page','1','--quote','Recovery page 01 source passage.','--comment','Synthetic fixture, unreviewed.');
  const preview=cli('preview','--annotation',annotation.annotation.id);
  cli('apply',preview.preview.id); cli('brief');
  await page.goto(opened.viewer_url);
  await ready(1,'Recovery');
  await page.getByRole('tab',{name:'Brief',exact:true}).click();
  const history=page.getByRole('region',{name:'Project changes and history',exact:true});
  const update=page.getByRole('button',{name:'Update brief from imported evidence',exact:true});
  await expect(history).toContainText('Brief matches the project at this check.');
  const initial=editions();
  await check('failed freshness clears current label and preserves editions',async()=>{
    const handler=route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Injected freshness service failure'})});
    await page.route('**/api/workflow/maintenance?*',handler);
    await history.getByRole('button',{name:'Check changes',exact:true}).click();
    await expect(history.getByRole('alert')).toContainText('Freshness could not be verified');
    await expect(history).not.toContainText('Brief matches the project at this check.');
    unchanged(initial); await screenshot('freshness-failed');
    await page.unroute('**/api/workflow/maintenance?*',handler);
    await history.getByRole('button',{name:'Check changes',exact:true}).click();
    await expect(history).toContainText('Brief matches the project at this check.');
    unchanged(initial);
  });
  await check('lost committed response retries the identical request without another edition',async()=>{
    const before=cli('history'); const requests=[]; let drop=true;
    const handler=async route=>{
      const body=route.request().postDataJSON();
      if(body.action!=='brief') return route.continue();
      requests.push(body);
      if(!drop) return route.continue();
      drop=false;
      const response=await route.fetch(); assert.equal(response.status(),200);
      fs.writeFileSync(path.join(output,'lost-response-body.json'),await response.body());
      await route.abort('failed');
    };
    await page.route('**/api/workflow',handler);
    await update.click();
    await expect(page.getByRole('region',{name:'Project brief',exact:true})).toContainText('Failed to fetch');
    const committed=cli('history'); assert.equal(committed.editions.length,before.editions.length+1);
    await update.click();
    await expect(page.getByRole('region',{name:'Project brief',exact:true})).toContainText('Project brief updated.');
    assert.equal(requests.length,2); assert.deepEqual(requests[0],requests[1]);
    assert.deepEqual(cli('history'),committed); unchanged(initial);
    await page.unroute('**/api/workflow',handler);
    await screenshot('lost-response-recovered');
    return {requests,editions:committed.editions.map(e=>e.id)};
  });
  await check('interrupted publication resumes its retained request after restart',async()=>{
    // Temporarily unavailable evidence storage causes a real interrupted generation.
    let requestId, obstruction;
    const handler=async route=>{
      const body=route.request().postDataJSON();
      if(body.action==='brief'&&!requestId) {
        requestId=body.request_id;
        obstruction=path.join(workspace,'rks','rks.sqlite3');
        fs.renameSync(obstruction,obstruction+'.held');
      }
      await route.continue();
    };
    await page.route('**/api/workflow',handler);
    await update.click();
    await expect(page.getByRole('region',{name:'Project brief',exact:true})).toContainText('Brief request retained');
    assert.ok(cli('history').pending_briefs.includes(requestId));
    await page.unroute('**/api/workflow',handler);
    fs.renameSync(obstruction+'.held',obstruction);
    cli('stop'); cli('resume','--no-open'); await page.reload();
    await page.getByRole('tab',{name:'Brief',exact:true}).click();
    await expect(history.getByRole('button',{name:'Resume this brief',exact:true})).toBeVisible();
    await history.getByRole('button',{name:'Resume this brief',exact:true}).click();
    await expect(history.getByRole('button',{name:'Resume this brief',exact:true})).toHaveCount(0);
    const after=cli('history'); assert.equal(after.editions.filter(e=>e.id===requestId).length,1);
    assert.equal(after.pending_briefs.length,0); unchanged(initial);
    await screenshot('interrupted-publication-recovered'); return {request_id:requestId};
  });
  await check('retrying an older edition leaves the latest edition current',async()=>{
    const before=cli('status').brief.id;
    const oldest=cli('history').editions.at(-1).id;
    const response=await page.request.post(new URL('/api/workflow',opened.viewer_url).href,
      {data:{action:'brief',session_id:opened.session_id,request_id:oldest}});
    assert.equal(response.status(),200); assert.equal(cli('status').brief.id,before); unchanged(initial);
    return {older:oldest,latest:before};
  });
}
async function reader() {
  const input=path.join(output,'long.pdf'); fs.writeFileSync(input,pdf(30,'Long document'));
  const second=path.join(output,'second.pdf'); fs.writeFileSync(second,pdf(1,'Second document'));
  const opened=cli('start',input,'--question','Long reader acceptance fixture','--no-open');
  cli('add',second);
  await page.goto(opened.viewer_url); await ready(1,'Long document');
  const samples=[]; receipt.raster_samples=samples;
  async function sample(number,zoom,direction) {
    await page.waitForFunction(()=>![...document.querySelectorAll('.pdf-document-container')].some(e=>e.querySelector('canvas')?.width>0&&e.getAttribute('aria-busy')==='true'));
    const data=await page.evaluate(()=>{
      const canvases=[...document.querySelectorAll('.pdf-document-container canvas')];
      const active=canvases.filter(c=>c.width>0&&c.height>0);
      return {placeholders:canvases.length,active:active.length,pixel_bytes:active.reduce((n,c)=>n+c.width*c.height*4,0),
        pages:active.map(c=>Number(c.parentElement.dataset.page)),zoom:document.querySelector('#zoomInfo').textContent,js_heap:performance.memory?.usedJSHeapSize??null};
    });
    samples.push({requested_page:number,mode:zoom,direction,...data}); assert.ok(data.active<=7,JSON.stringify(data));
  }
  for(const zoom of ['fit_width','100_percent']) {
    await check(`all 30 pages both directions at ${zoom}`,async()=>{
      if(zoom==='fit_width') await page.locator('#fitWidthBtn').click();
      else {
        // Restore a user preference at exactly 100%; toolbar increments are relative to fit scale.
        await page.evaluate(()=>{
          const key='apw:reading-progress:v1', map=JSON.parse(localStorage.getItem(key));
          for(const value of Object.values(map)) {value.zoom=1;value.zoomMode='manual';value.lastPage=1;}
          localStorage.setItem(key,JSON.stringify(map));
        });
        await page.reload(); await expect(page.locator('#zoomInfo')).toHaveText('100%');
      }
      for(const direction of ['forward','backward']) {
        const numbers=Array.from({length:30},(_,i)=>direction==='forward'?i+1:30-i);
        for(const number of numbers) {
          await page.locator(`.pdf-document-container[data-page="${number}"]`).evaluate(el=>el.scrollIntoView({block:'start'}));
          await ready(number,`page ${String(number).padStart(2,'0')} source passage`);
          await sample(number,zoom,direction);
        }
      }
      await screenshot(`scroll-${zoom}`); return {visits:60};
    });
  }
  await check('long-document search, next/previous matches and direct page jumps',async()=>{
    await page.locator('#findInDocumentBtn').click();
    await page.locator('#searchInput').fill('Shared search marker'); await page.locator('#searchBtn').click();
    await expect(page.locator('#searchInfo')).toContainText('30'); await ready(1,'Long document');
    for(let n=2;n<=30;n++) {await page.locator('#searchNextBtn').click();await ready(n,'Long document');}
    await page.locator('#searchNextBtn').click();await ready(1,'Long document');
    await page.locator('#searchPrevBtn').click();await ready(30,'Long document');
    await page.locator('#searchInput').fill('page 17 source');await page.locator('#searchBtn').click();await ready(17,'page 17');
    await page.locator('#searchInput').press('Escape');
    for(const number of [1,15,30,7]) await jump(number,`page ${String(number).padStart(2,'0')}`);
    await screenshot('search-and-jumps');
  });
  await check('highlights on pages 2, 15 and 29 retain their exact page and quote',async()=>{
    await page.getByText('Highlight tools & comments',{exact:true}).click();
    for(const number of [2,15,29]) {
      const target=await jump(number,`page ${String(number).padStart(2,'0')}`);
      const before=await page.locator('#annotationList .annotation-select').count();
      await target.locator('.text-layer span').first().evaluate(span=>{
        const range=document.createRange();range.selectNodeContents(span);
        const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
      });
      await page.locator('#highlightBtn').click();
      await expect(page.locator('#annotationList')).toContainText(`Long document page ${String(number).padStart(2,'0')}`);
      await expect(page.locator('#annotationList .annotation-select')).toHaveCount(before+1);
    }
    const response=await page.request.get(new URL(`/api/annotations?session_id=${opened.session_id}`,opened.viewer_url).href);
    assert.equal(response.status(),200);
    const annotations=(await response.json()).annotations.map(i=>i.annotation);
    assert.deepEqual(annotations.map(i=>i.page).sort((a,b)=>a-b),[2,15,29]);
    for(const item of annotations) assert.equal(item.quote,`Long document page ${String(item.page).padStart(2,'0')} source passage.`);
    receipt.annotations=annotations; await screenshot('long-document-annotations');
  });
  await check('zoom preserves the current page and paper switching clears old rasters',async()=>{
    await jump(15,'page 15');
    await page.locator('#zoomInBtn').click();await expect(page.locator('#zoomInfo')).toHaveText('120%');await ready(15,'page 15');
    await page.locator('#zoomOutBtn').click();await expect(page.locator('#zoomInfo')).toHaveText('100%');await ready(15,'page 15');
    const navigation=page.getByRole('navigation',{name:'Project papers'});
    await navigation.getByRole('link',{name:/second/}).click();
    await expect(page.locator('.pdf-document-container')).toHaveCount(1);await ready(1,'Second document');
    assert.equal(await page.locator('.text-layer').filter({hasText:'Long document'}).count(),0);
    await expect(page.locator('#annotationList')).not.toContainText('Long document');
    await expect(page.locator('#zoomInfo')).toHaveText('100%');
    await navigation.getByRole('link',{name:/long/}).click();await ready(15,'page 15');
    await expect(page.locator('#annotationList')).toContainText('page 29');
    await page.reload();await ready(15,'page 15');await expect(page.locator('#zoomInfo')).toHaveText('100%');
    await screenshot('paper-return');
  });
}
async function citations() {
  const input=JSON.parse(fs.readFileSync(path.join(citationInput,'citations.json'),'utf8'));
  workspace=input.workspace;
  const opened=cli('resume','--no-open');
  const origin=new URL(opened.viewer_url).origin;
  const sources=input.cases.map(c=>({...c,url:c.passage.url}));
  assert.equal(sources.length,10);assert.equal(new Set(sources.map(s=>s.annotation_id)).size,10);
  for(const stage of ['initial','after_restart']) {
    if(stage==='after_restart') {cli('stop');cli('resume','--no-open');}
    for(const source of sources) await check(`${stage}: ${source.case_id}`,async()=>{
      const url=new URL(source.url);url.host=new URL(origin).host;
      assert.equal(url.searchParams.get('document_sha256'),source.document_sha256);
      await page.goto(url.href);
      await expect(page.locator('#statusText')).toContainText('passage ready');
      await ready(source.page);
      await expect(page.locator('.annotation-mark.selected').first()).toBeVisible();
      const selected=page.locator('#annotationList .selected');
      await expect(selected).toContainText(source.quote);
      await screenshot(`${stage}-${source.case_id}`);
      return {document_sha256:source.document_sha256,page:source.page,quote:source.quote,
        original_receipt_sha256:source.original_receipt_sha256,highlight_rects:await page.locator('.annotation-mark.selected').count()};
    });
  }
  const source=sources[0];
  for(const [field,value] of [['document_sha256','0'.repeat(64)],['annotation_id','ann_missing'],['page','999'],['passage_sha256','0'.repeat(64)]]) {
    await check(`reject changed ${field}`,async()=>{
      const url=new URL(source.url);url.searchParams.set(field,value);
      await page.goto(url.href);
      await expect(page.locator('#statusText')).toContainText(/changed|missing|outside|does not|not found|match|failed|unavailable|different/i);
      await expect(page.locator('#statusText')).not.toContainText('passage ready');
      await screenshot(`rejected-${field}`);
      return {status:await page.locator('#statusText').textContent()};
    });
  }
  const originalUrl=new URL(source.url);
  const session=originalUrl.searchParams.get('session_id');
  const api=pathname=>new URL(pathname,origin).href;
  const stored=await (await page.request.get(api(`/api/annotations?session_id=${session}`))).json();
  const annotation=stored.annotations.find(r=>r.annotation.id===source.annotation_id).annotation;
  const postAnnotation=async value=>{
    const response=await page.request.post(api('/api/annotations'),{data:{session_id:session,annotation:value}});
    assert.ok(response.ok(),`Annotation save failed: ${response.status()}`);
  };
  await check('edited and deleted real anchor reject the old citation',async()=>{
    try {
      await postAnnotation({...annotation,quote:'Changed fixture quotation.',anchor:null});
      await page.goto(source.url);await expect(page.locator('#statusText')).toContainText('Cited passage has changed');
      await page.request.post(api('/api/annotations/delete'),{data:{session_id:session,annotation_id:source.annotation_id}});
      await page.goto(source.url);await expect(page.locator('#statusText')).toContainText('missing or deleted');
      await expect(page.locator('.annotation-mark.selected')).toHaveCount(0);
    } finally {await postAnnotation(annotation);}
  });
  for(const fault of ['changed','missing']) await check(`${fault} real PDF fails explicitly`,async()=>{
    const file=input.papers.find(p=>p.key===source.paper).source_pdf;
    assert.ok(path.resolve(file).startsWith(path.resolve(workspace)+path.sep));
    const original=fs.readFileSync(file);
    try {
      if(fault==='changed') fs.appendFileSync(file,'\n% deliberate acceptance source change\n');
      else fs.renameSync(file,file+'.held');
      await page.goto(source.url);
      await expect(page.locator('#statusText')).toContainText(/Source PDF changed|missing|not found|unavailable|does not exist|could not/i);
      await expect(page.locator('.annotation-mark.selected')).toHaveCount(0);
      await screenshot(`source-${fault}`);
      return {status:await page.locator('#statusText').textContent()};
    } finally {
      if(fault==='changed') fs.writeFileSync(file,original);else fs.renameSync(file+'.held',file);
      assert.equal(hash(file),source.document_sha256);
    }
  });
  await check('valid source with an unmatched quote retains the paper and quotation',async()=>{
    const quote='This deliberate acceptance quotation does not occur in the original paper.';
    const updated={...annotation,quote,anchor:null};
    try {
      await postAnnotation(updated);
      const passage={annotation_id:annotation.id,page:annotation.page,quote,anchor:null,rects:annotation.rects};
      const sha=execFileSync(python,['-c','import sys,json,hashlib; print(hashlib.sha256(json.dumps(json.load(sys.stdin),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest())'],{input:JSON.stringify(passage),encoding:'utf8'}).trim();
      const url=new URL(source.url);url.searchParams.set('passage_sha256',sha);
      await page.goto(url.href);await expect(page.locator('#statusText')).toContainText('missing or ambiguous');
      await ready(source.page);await expect(page.locator('.text-layer span').first()).toBeVisible();
      await expect(page.locator('#annotationList')).toContainText(quote);
      await expect(page.locator('.annotation-mark.selected')).toHaveCount(0);
      await screenshot('unmatched-quote-retains-paper');
    } finally {await postAnnotation(annotation);}
  });
  await check('original citation works again after restoring the fault fixtures',async()=>{
    await page.goto(source.url);await expect(page.locator('#statusText')).toContainText('passage ready');
    await expect(page.locator('.annotation-mark.selected').first()).toBeVisible();
  });
}
async function edges() {
  const input=path.join(output,'ambiguous-long.pdf');fs.writeFileSync(input,pdf(30,'Repeated document',true));
  const opened=cli('start',input,'--question','Reader rejection and late-response fixtures','--no-open');
  for(const [number,quote,message] of [[17,'Shared search marker on every page.','missing or ambiguous'],[99,'outside source','outside this PDF']]) {
    await check(`valid citation contract rejects ${number===17?'ambiguous quotation':'out-of-range page'}`,async()=>{
      const created=cli('annotate','--page',number,'--quote',quote,'--comment','Deliberate engineering fault fixture.');
      const sha=execFileSync(python,['-c','import sys,json; from agent_pdf_workbench.passage import annotation_passage; from agent_pdf_workbench.evidence import digest; print(digest(annotation_passage(json.load(sys.stdin))))'],{input:JSON.stringify(created.annotation),encoding:'utf8'}).trim();
      const url=new URL(opened.viewer_url);
      for(const [key,value] of Object.entries({document_sha256:opened.document_sha256,annotation_id:created.annotation.id,page:number,passage_sha256:sha})) url.searchParams.set(key,String(value));
      await page.goto(url.href);await expect(page.locator('#statusText')).toContainText(message);
      await expect(page.locator('.annotation-mark.selected')).toHaveCount(0);
      await expect(page.locator('#annotationList')).toContainText(quote);
      if(number===17) await ready(17,'Repeated document');
      await screenshot(`rejected-page-${number}`);
    });
  }
  await check('a late previous-paper freshness response cannot replace the current paper state',async()=>{
    const annotation=cli('annotate','--page','1','--quote','Repeated document page 01 source passage.');
    const preview=cli('preview','--annotation',annotation.annotation.id);cli('apply',preview.preview.id);cli('brief');
    const second=path.join(output,'second.pdf');fs.writeFileSync(second,pdf(1,'Second document'));cli('add',second);
    await page.goto(opened.viewer_url);await ready(1,'Repeated document');
    await page.getByRole('tab',{name:'Brief',exact:true}).click();
    const history=page.getByRole('region',{name:'Project changes and history',exact:true});
    await expect(history).toContainText('Your saved brief is outdated.');
    let release, captured, finished;
    const hold=new Promise(resolve=>{release=resolve;});
    const received=new Promise(resolve=>{captured=resolve;});
    const done=new Promise(resolve=>{finished=resolve;});
    const handler=async route=>{
      if(new URL(route.request().url()).searchParams.get('session_id')!==opened.session_id) return route.continue();
      const response=await route.fetch();const payload=await response.json();captured(payload);
      await hold;await route.fulfill({response});finished();
    };
    await page.route('**/api/workflow/maintenance?*',handler);
    try {
      await history.getByRole('button',{name:'Check changes',exact:true}).click();
      const delayed=await received;assert.equal(delayed.freshness,'outdated');
      cli('brief');
      await page.getByRole('navigation',{name:'Project papers'}).getByRole('link',{name:/second/}).click();
      await ready(1,'Second document');
      await expect(history).toContainText('Brief matches the project at this check.');
      release();await done;await page.waitForTimeout(250);
      await expect(history).toContainText('Brief matches the project at this check.');
      await expect(history).not.toContainText('Your saved brief is outdated.');
      await expect(page.locator('.text-layer')).toContainText('Second document');
      await screenshot('late-response-ignored');return {delayed_freshness:delayed.freshness,current_freshness:'current'};
    } finally {release();await page.unroute('**/api/workflow/maintenance?*',handler);}
  });
}
try {
  browser=await chromium.launch({headless:true});
  page=await browser.newPage({viewport:{width:1440,height:1000}});
  receipt.chromium_version=browser.version();
  page.on('pageerror',error=>receipt.errors.push(String(error)));
  await ({recovery,reader,citations,edges}[mode])();
  assert.deepEqual(receipt.errors,[]);receipt.passed=true;
} catch(error) {
  receipt.failure=String(error.stack??error);
  if(page) await screenshot('failure').catch(()=>{});
  process.exitCode=1;
} finally {
  if(browser) await browser.close();
  if(fs.existsSync(path.join(workspace,'workspace.json'))) {
    try {cli('stop');} catch(error) {receipt.cleanup_error=String(error);receipt.passed=false;process.exitCode=1;}
  }
  save();console.log(JSON.stringify({mode,passed:receipt.passed,checks:receipt.checks.map(c=>({name:c.name,passed:c.passed})),failure:receipt.failure},null,2));
}
