/* Focused negative regressions for immutable export and popup acceptance. */
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { validExport, observePages, noAdditionalPages, observeWindowOpen } = require('./check_ui.cjs');

async function main() {
  const complete = [
    { record: 'r2', title: 'Pocket placement', owner: 'Lee', amount: '$45.00', state: 'ready' },
    { record: 'r4', title: 'Trim approval', owner: 'Noah', amount: '$18.50', state: 'ready' },
  ];
  assert.equal(validExport(complete), true);
  assert.equal(validExport([...complete].reverse()), true);
  assert.equal(validExport(['Pocket placement', 'Trim approval']), false);
  assert.equal(validExport(complete.map(({ title }) => ({ title }))), false);
  for (const field of ['record', 'title', 'owner', 'amount', 'state']) {
    assert.equal(validExport(complete.map(record => {
      const reduced = { ...record };
      delete reduced[field];
      return reduced;
    })), false, `Missing ${field} must fail`);
  }
  assert.equal(validExport([{ ...complete[0], amount: '$0.00' }, complete[1]]), false);
  assert.equal(validExport([{ ...complete[0], state: 'review' }, complete[1]]), false);
  assert.equal(validExport([complete[0], complete[0]]), false);
  const context = new EventEmitter();
  const observed = observePages(context);
  const initialPage = new EventEmitter();
  context.emit('page', initialPage);
  assert.equal(noAdditionalPages(observed, 1), true);
  const popup = new EventEmitter();
  context.emit('page', popup);
  initialPage.emit('popup', popup);
  popup.emit('close');
  assert.equal(noAdditionalPages(observed, 1), false, 'Closing a popup must not erase history');
  assert.equal(observed.createdPages, 2);
  assert.equal(observed.popupEvents, 1);

  let browserEvidence = 'not_requested';
  const [playwrightModule, browserExecutable] = process.argv.slice(2);
  if (playwrightModule) {
    const { chromium } = require(playwrightModule);
    const launch = { headless: true };
    if (browserExecutable) launch.executablePath = browserExecutable;
    const browser = await chromium.launch(launch);
    try {
      const liveContext = await browser.newContext();
      try {
        const liveObserved = observePages(liveContext);
        await observeWindowOpen(liveContext, liveObserved);
        const page = await liveContext.newPage();
        await page.goto('data:text/html,<button id="probe">Probe</button><script>document.querySelector("%23probe").onclick=()=>{const child=window.open("about:blank");if(child)child.close();}</script>');
        await page.click('#probe');
        await page.evaluate(() => Promise.resolve());
        assert.equal(liveObserved.windowOpenCalls, 1, 'Capture an immediate open-and-close attempt');
        assert.equal(noAdditionalPages(liveObserved, liveContext.pages().length), false);
        browserEvidence = { headless: true, ...liveObserved, currentPages: liveContext.pages().length };
      } finally {
        await liveContext.close();
      }
    } finally {
      await browser.close();
    }
  }
  process.stdout.write(JSON.stringify({ status: 'pass', exportChecks: 12, popupHistoryChecks: 4, browserEvidence }) + '\n');
}

main().catch(error => {
  process.stdout.write(JSON.stringify({ status: 'fail', error: error.message }) + '\n');
  process.exitCode = 1;
});
