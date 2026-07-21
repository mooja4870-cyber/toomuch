const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  console.log('Navigating to Streamlit...');
  await page.goto('http://localhost:8503', { waitUntil: 'networkidle0' });
  
  // Wait for tabs to render
  await page.waitForSelector('[data-testid="stTabs"]');
  
  // Get HTML of the tabs
  const tabsHTML = await page.evaluate(() => {
    return document.querySelector('[data-testid="stTabs"]').innerHTML;
  });
  
  console.log('--- TABS HTML ---');
  console.log(tabsHTML);
  
  await browser.close();
})();
