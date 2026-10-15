// Screen-record the real demo page (server.py on :8000) running one live agent run.
//   node live.js [out.mp4]      (needs: docker FalkorDB, python server.py, OPENAI_API_KEY for the server)
const path = require("path");
const puppeteer = require("puppeteer-core");
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const FFDIR = "C:/Users/avina/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-essentials_build/bin";
process.env.PATH = FFDIR + path.delimiter + process.env.PATH;
const OUT = path.resolve(process.argv[2] || "live.webm");

(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: "new", args: ["--hide-scrollbars"] });
  const page = await browser.newPage();
  page.on("pageerror", e => console.log("pageerror:", e.message));
  await page.setViewport({ width: 1920, height: 1080 });
  await page.evaluateOnNewDocument(() => { document.addEventListener("DOMContentLoaded", () => { document.body.style.zoom = "1.25"; }); });
  await page.goto("http://localhost:8000", { waitUntil: "networkidle0" });
  await page.evaluate(async () => {
    const sel = document.getElementById("scenario");
    sel.value = [...sel.options].find(o => o.text.includes("remove c.lee → payroll")).value;
    await sel.onchange();
    document.getElementById("inject").checked = true;
  });
  const rec = await page.screencast({ path: OUT });
  await new Promise(r => setTimeout(r, 1500));
  await page.click("#run");
  await page.waitForFunction(() => !document.getElementById("run").disabled, { timeout: 180000, polling: 250 });
  // Screencasts only emit frames on repaint; keep repainting so the final state is captured.
  await page.evaluate(() => { const d = document.createElement("div"); d.style.cssText = "position:fixed;width:1px;height:1px;left:0;top:0"; document.body.append(d); let k = 0; setInterval(() => { d.style.background = (k++ % 2) ? "#f5f5f7" : "#f6f5f1"; }, 40); });
  await new Promise(r => setTimeout(r, 3500));
  console.log("outcome:", await page.$eval("#outcome", e => e.textContent));
  await rec.stop();
  await browser.close();
  console.log("wrote", OUT);
})();
