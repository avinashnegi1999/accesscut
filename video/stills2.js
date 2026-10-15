// Screenshot film2.html at chosen seconds, for checking layout before a full render.
//   node stills.js 4 16 40   ->  still-4.png still-16.png still-40.png
const path = require("path");
const puppeteer = require("puppeteer-core");
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";

(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: "new", args: ["--hide-scrollbars"] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto("file:///" + path.join(__dirname, process.env.FILM || "film2.html").replace(/\\/g, "/") + "?record", { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);
  for (const t of process.argv.slice(2)) {
    await page.evaluate(async (s) => { await window.render(s); }, Number(t));
    await page.screenshot({ path: `still-${t}.png` });
  }
  await browser.close();
})();
