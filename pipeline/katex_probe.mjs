import { createRequire } from "module";

const require = createRequire(import.meta.url);
const katex = require("C:/Users/tempo/Downloads/EduBlast/Web/node_modules/katex");
const tex = process.argv[2] || "";
katex.renderToString(tex, { throwOnError: true, displayMode: false });
