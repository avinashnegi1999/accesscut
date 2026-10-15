// Screenshot a static page at 1920x1080:  node shot.js page.html out.png
const path = require("path");
const puppeteer = require("puppeteer-core");
(async () => {
  const b = await puppeteer.launch({ executablePath: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless: "new" });
  const pg = await b.newPage();
  await pg.setViewport({ width: 1920, height: 1080 });
  await pg.goto("file:///" + path.join(__dirname, process.argv[2]).split(path.sep).join("/"), { waitUntil: "networkidle0" });
  await pg.evaluate(() => document.fonts.ready);
  await pg.screenshot({ path: process.argv[3] });
  await b.close();
})();
