/* Immutable headless behavioral/layout acceptance, independent of candidate source. */
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

const READY_EXPORT = [
  { record: 'r2', title: 'Pocket placement', owner: 'Lee', amount: '$45.00', state: 'ready' },
  { record: 'r4', title: 'Trim approval', owner: 'Noah', amount: '$18.50', state: 'ready' },
];

function validExport(records, expected = READY_EXPORT) {
  if (!Array.isArray(records) || records.length !== expected.length) return false;
  if (records.some(record => record === null || typeof record !== 'object' || Array.isArray(record))) return false;
  if (new Set(records.map(record => record.record)).size !== expected.length) return false;
  return expected.every(reference => {
    const record = records.find(candidate => candidate.record === reference.record);
    return record && Object.entries(reference).every(([field, value]) => record[field] === value);
  });
}

function observePages(context) {
  const observed = { createdPages: 0, popupEvents: 0, windowOpenCalls: 0 };
  context.on('page', page => {
    observed.createdPages += 1;
    page.on('popup', () => { observed.popupEvents += 1; });
  });
  return observed;
}

function noAdditionalPages(observed, currentPageCount) {
  return observed.createdPages === 1 && observed.popupEvents === 0 && observed.windowOpenCalls === 0 && currentPageCount === 1;
}

async function observeWindowOpen(context, observed) {
  // Record attempts as well as page events: a synchronously closed popup can
  // disappear before Playwright finishes initializing its page object.
  await context.exposeBinding('__benchmarkObserveWindowOpen', () => { observed.windowOpenCalls += 1; });
  await context.addInitScript(() => {
    const originalOpen = window.open;
    window.open = function (...args) {
      void window.__benchmarkObserveWindowOpen().catch(() => {});
      return Reflect.apply(originalOpen, this, args);
    };
  });
}

async function main() {
  const [workspace, outputDirectory, playwrightModule, browserExecutable] = process.argv.slice(2);
  if (!workspace || !outputDirectory || !playwrightModule) {
    throw new Error('Usage: node check_ui.cjs WORKSPACE OUTPUT_DIRECTORY PLAYWRIGHT_MODULE [BROWSER_EXECUTABLE]');
  }
  const { chromium } = require(playwrightModule);
  fs.mkdirSync(outputDirectory, { recursive: true });
  const launch = { headless: true };
  if (browserExecutable) launch.executablePath = browserExecutable;
  const browser = await chromium.launch(launch);
  const evidence = { status: 'pass', headless: true, widths: [], checks: [] };
  const requireCheck = (name, pass, detail) => {
    evidence.checks.push({ name, pass, detail });
    if (!pass) evidence.status = 'fail';
  };
  try {
    for (const width of [1440, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, acceptDownloads: true, deviceScaleFactor: 1 });
      try {
        const observedPages = observePages(context);
        await observeWindowOpen(context, observedPages);
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(pathToFileURL(path.resolve(workspace, 'index.html')).href);
        const geometry = await page.evaluate(() => {
          const rect = node => {
            const r = node.getBoundingClientRect();
            return { x: r.x, y: r.y, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
          };
          const visible = node => node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden' && getComputedStyle(node).display !== 'none';
          const inside = (child, owner) => child.x >= owner.x - 1 && child.right <= owner.right + 1 && child.y >= owner.y - 1 && child.bottom <= owner.bottom + 1;
          const overlaps = (a, b) => Math.min(a.right, b.right) - Math.max(a.x, b.x) > 1 && Math.min(a.bottom, b.bottom) - Math.max(a.y, b.y) > 1;
          const label = node => `${node.tagName.toLowerCase()}${node.id ? '#' + node.id : ''}: ${node.textContent.trim().slice(0, 60)}`;
          const textContained = node => {
            const range = document.createRange();
            range.selectNodeContents(node);
            return [...range.getClientRects()].every(r => inside(r, rect(node)));
          };
          const headerNodes = ['#brand', '#add', '#export'].map(selector => document.querySelector(selector));
          const headerRects = headerNodes.map(rect);
          const header = rect(document.querySelector('#header'));
          const centers = headerRects.map(r => r.y + r.height / 2);
          const controls = [...document.querySelectorAll('button,select')].filter(visible).map(node => ({ label: label(node), ...rect(node), font: parseFloat(getComputedStyle(node).fontSize), textContained: textContained(node) }));
          const panels = [...document.querySelectorAll('.panel')];
          const escaped = panels.flatMap(panel => [...panel.querySelectorAll('*')].filter(visible).filter(node => !inside(rect(node), rect(panel))).map(label));
          const rows = [...document.querySelectorAll('#rows .row')].filter(visible).map(row => {
            const title = row.querySelector('.title');
            const details = row.querySelector('.details');
            const fields = ['.title', '.owner', '.amount', '.badge'].map(selector => row.querySelector(selector));
            return { record: row.dataset.record, state: row.dataset.state, ...rect(row), text: row.innerText, readable: fields.every(node => visible(node) && parseFloat(getComputedStyle(node).fontSize) >= 14 && textContained(node)), overlap: overlaps(rect(title), rect(details)), fields: fields.map(node => node.textContent.trim()) };
          });
          const work = rect(document.querySelector('#work-panel'));
          const summary = rect(document.querySelector('#summary-panel'));
          const title = document.querySelector('h1');
          const toolbar = document.querySelector('.toolbar');
          const toolbarChildren = [...toolbar.children].map(rect);
          return {
            width: innerWidth, pageWidth: document.documentElement.scrollWidth,
            headerOneRow: Math.max(...centers) - Math.min(...centers) <= 3 && headerRects.every(r => inside(r, header)),
            headerOverlap: headerRects.some((a, i) => headerRects.slice(i + 1).some(b => overlaps(a, b))),
            headerHeight: header.height, headingFont: parseFloat(getComputedStyle(title).fontSize),
            controls, escaped, rows,
            desktopPanelAlignment: innerWidth < 1000 || Math.abs(work.y - summary.y) <= 1,
            toolbarInline: toolbarChildren.length === 2 && Math.abs((toolbarChildren[0].y + toolbarChildren[0].height / 2) - (toolbarChildren[1].y + toolbarChildren[1].height / 2)) <= 4,
            pageHeight: document.documentElement.scrollHeight,
          };
        });
        evidence.widths.push(geometry);
        requireCheck(`${width}: contained horizontal header`, geometry.headerOneRow && !geometry.headerOverlap && geometry.headerHeight <= 72, geometry.headerHeight);
        requireCheck(`${width}: page and panel containment`, geometry.pageWidth <= width && geometry.escaped.length === 0, geometry.escaped);
        requireCheck(`${width}: readable controls and title`, geometry.controls.every(control => control.height >= 40 && control.font >= 14 && control.textContained) && geometry.headingFont >= 14 && geometry.headingFont <= 28, geometry.controls);
        requireCheck(`${width}: original records visible and readable`, geometry.rows.length === 4 && geometry.rows.every(row => row.readable && !row.overlap), geometry.rows);
        requireCheck(`${width}: compact rows`, geometry.rows.every(row => row.height <= (width >= 1000 ? 64 : 96)), geometry.rows.map(row => row.height));
        requireCheck(`${width}: alignment and inline toolbar`, geometry.desktopPanelAlignment && geometry.toolbarInline, { aligned: geometry.desktopPanelAlignment, toolbarInline: geometry.toolbarInline });
        const originals = [
          ['r1', 'review', 'Sleeve measurements', 'Maya', '$120.10', 'Review'],
          ['r2', 'ready', 'Pocket placement', 'Lee', '$45.00', 'Ready'],
          ['r3', 'review', 'Construction review with extended reference notes', 'Ari', '$80.25', 'Review'],
          ['r4', 'ready', 'Trim approval', 'Noah', '$18.50', 'Ready'],
        ];
        requireCheck(`${width}: original content preserved`, JSON.stringify(geometry.rows.map(row => [row.record, row.state, ...row.fields])) === JSON.stringify(originals));
        await page.screenshot({ path: path.join(outputDirectory, `ui-${width}.png`), fullPage: true });
        await page.selectOption('#filter', 'review');
        const reviews = await page.locator('#rows .row:visible').evaluateAll(rows => rows.map(row => row.dataset.record));
        requireCheck(`${width}: review filter`, JSON.stringify(reviews) === JSON.stringify(['r1', 'r3']), reviews);
        await page.selectOption('#filter', 'ready');
        const ready = await page.locator('#rows .row:visible').evaluateAll(rows => rows.map(row => row.dataset.record));
        requireCheck(`${width}: ready filter`, JSON.stringify(ready) === JSON.stringify(['r2', 'r4']), ready);
        try {
          const downloadPromise = page.waitForEvent('download', { timeout: 2500 });
          await page.click('#export');
          const download = await downloadPromise;
          const downloadPath = path.join(outputDirectory, `export-${width}.json`);
          await download.saveAs(downloadPath);
          const records = JSON.parse(fs.readFileSync(downloadPath, 'utf8'));
          requireCheck(`${width}: export visible rows`, validExport(records), records);
        } catch (error) {
          requireCheck(`${width}: export visible rows`, false, error.message);
        }
        await page.click('#add');
        const visibleRows = await page.locator('#rows .row:visible').allTextContents();
        const feedback = await page.locator('#feedback').innerText();
        requireCheck(`${width}: add draft resets filter and announces`, await page.locator('#filter').inputValue() === 'all' && visibleRows.length === 5 && visibleRows.filter(text => text.includes('New draft')).length === 1 && /draft|added|created/i.test(feedback), { rows: visibleRows.length, feedback });
        await page.selectOption('#filter', 'review');
        await page.selectOption('#filter', 'all');
        requireCheck(`${width}: all restores rows`, await page.locator('#rows .row:visible').count() === 5);
        requireCheck(`${width}: no script errors`, errors.length === 0, errors);
        requireCheck(`${width}: no popup throughout interaction`, noAdditionalPages(observedPages, context.pages().length), { ...observedPages, currentPages: context.pages().length });
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(outputDirectory, 'ui.json'), JSON.stringify(evidence, null, 2) + '\n');
  process.stdout.write(JSON.stringify(evidence) + '\n');
  process.exitCode = evidence.status === 'pass' ? 0 : 1;
}

module.exports = { validExport, observePages, noAdditionalPages, observeWindowOpen };
if (require.main === module) {
  main().catch(error => {
    process.stdout.write(JSON.stringify({ status: 'fail', error: error.message }) + '\n');
    process.exitCode = 1;
  });
}
