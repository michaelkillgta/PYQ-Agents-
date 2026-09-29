import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
const katex = require("C:/Users/tempo/Downloads/EduBlast/Web/node_modules/katex");
const items = JSON.parse(fs.readFileSync(0, "utf8"));
const out = [];
for (const tex of items) {
  try {
    katex.renderToString(tex, { throwOnError: true, displayMode: false });
    out.push(true);
  } catch {
    out.push(false);
  }
}
process.stdout.write(JSON.stringify(out));
