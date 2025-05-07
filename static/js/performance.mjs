// static/js/performance.mjs

// 1) Import Lighthouse
import lighthouse from 'lighthouse';

// 2) Import il named export launch (non default)
import { launch } from 'chrome-launcher';

async function runLighthouse(url) {
  // 3) usa launch() direttamente
  const chrome = await launch({ chromeFlags: ['--headless'] });
  const options = { port: chrome.port, output: 'json', logLevel: 'error' };
  const runnerResult = await lighthouse(url, options);
  await chrome.kill();

  const lhr = runnerResult.lhr;
  return {
    FCP: lhr.audits['first-contentful-paint'].numericValue,
    LCP: lhr.audits['largest-contentful-paint'].numericValue,
    CLS: lhr.audits['cumulative-layout-shift'].numericValue,
    TBT: lhr.audits['total-blocking-time'].numericValue,
    SI: lhr.audits['speed-index'].numericValue,
    TTI: lhr.audits['interactive'].numericValue,
    score: lhr.categories.performance.score * 100
  };
}

const url = process.argv[2];
if (!url) {
  console.error('Usage: node performance.mjs <url>');
  process.exit(1);
}

try {
  const metrics = await runLighthouse(url);
  console.log(JSON.stringify(metrics));
} catch (err) {
  console.error(err);
  process.exit(1);
}
