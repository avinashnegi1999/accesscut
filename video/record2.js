// Records film2.html frame by frame with the installed Edge and pipes the
// frames straight into ffmpeg (no PNGs on disk).
//   node record.js [fps] [out.mp4]
const { spawn } = require("child_process");
const path = require("path");
const puppeteer = require("puppeteer-core");

const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const FFMPEG = process.env.FFMPEG || "C:/Users/avina/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe";
const FPS = Number(process.argv[2] || 30);
const OUT = path.resolve(process.argv[3] || "accesscut-film-v2.mp4");

(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: "new", args: ["--hide-scrollbars"] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto("file:///" + path.join(__dirname, process.env.FILM || "film2.html").replace(/\\/g, "/") + "?record", { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * FPS);

  const ff = spawn(FFMPEG, ["-y", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "png", "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18", "-movflags", "+faststart", OUT],
    { stdio: ["pipe", "ignore", "inherit"] });

  const started = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate(async (t) => { await window.render(t); }, i / FPS);
    const png = await page.screenshot({ type: "png" });
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once("drain", r));
    if (i % (FPS * 5) === 0) process.stdout.write(`frame ${i}/${frames}  ${((Date.now() - started) / 1000).toFixed(0)}s\n`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  await browser.close();
  console.log("wrote", OUT);
})();
