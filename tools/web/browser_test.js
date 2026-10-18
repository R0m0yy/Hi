// Plays the web build in a real Chromium (software WebGL via SwiftShader):
// opens the page, clicks Play, starts a new game, walks, and saves screenshots.
//   cd build/web_artifact && python3 -m http.server 8767 &
//   PW=/path/to/playwright OUT=/abs/dir node tools/web/browser_test.js
// Slow on a machine without a GPU (about one frame per second), so the waits are long.
const { chromium } = require(process.env.PW);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
  const logs = [];
  p.on('console', m => logs.push(m.type() + ': ' + m.text().slice(0, 300)));
  p.on('pageerror', e => logs.push('PAGEERROR: ' + e.message.slice(0, 300)));
  await p.goto(process.env.URL || 'http://127.0.0.1:8767/index.html', { waitUntil: 'load' });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: process.env.OUT + '/play_0_before.png' });
  console.log('overflow', await p.evaluate(() => document.documentElement.scrollWidth - innerWidth));
  await p.click('#play');
  const t0 = Date.now();
  try { await p.waitForSelector('#overlay', { state: 'hidden', timeout: 240000 }); } catch (e) { console.log('overlay still visible after 240 s'); }
  console.log('start took', ((Date.now() - t0) / 1000).toFixed(0), 's');
  console.log('status:', await p.textContent('#status'), '| notice hidden:', await p.evaluate(() => document.querySelector('#notice').hidden));
  await p.waitForTimeout(20000);
  await p.screenshot({ path: process.env.OUT + '/play_1_title.png' });
  const box = await (await p.$('#canvas')).boundingBox();
  await p.mouse.click(box.x + box.width * 0.22, box.y + box.height * (436 / 720));
  await p.waitForTimeout(25000);
  await p.screenshot({ path: process.env.OUT + '/play_2_newgame.png' });
  await p.keyboard.down('KeyD');
  await p.waitForTimeout(8000);
  await p.keyboard.up('KeyD');
  await p.waitForTimeout(6000);
  await p.screenshot({ path: process.env.OUT + '/play_3_moved.png' });
  console.log(logs.filter(l => !/^log: (Godot Engine|OpenGL|WebGL)/.test(l)).slice(0, 40).join('\n'));
  await b.close();
})();
