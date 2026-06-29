#!/usr/bin/env node

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const candidates = [
  path.resolve(scriptDir, "../dist/aimv.cjs"),
  path.resolve(scriptDir, "../dist/index.js"),
];
const entry = candidates.find((candidate) => fs.existsSync(candidate));

if (!entry) {
  console.error("海绵音乐 Skill 启动失败：未找到 dist/aimv.cjs 或 dist/index.js。");
  process.exit(1);
}

try {
  if (entry.endsWith(".cjs")) {
    createRequire(import.meta.url)(entry);
  } else {
    await import(pathToFileURL(entry).href);
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
