#!/usr/bin/env node
/**
 * Founder Preview preflight — fails before DevTools Preview if phone would hit localhost.
 * Run: npm run preview:preflight (from miniapp/)
 */
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const miniappRoot = path.join(__dirname, "..");
const localConfigPath = path.join(miniappRoot, "config.local.ts");

if (!existsSync(localConfigPath)) {
  console.error("Preview preflight FAILED: missing miniapp/config.local.ts");
  console.error('Copy config.example.ts → config.local.ts and set apiProfile: "qa".');
  process.exit(1);
}

try {
  execSync("node --import tsx scripts/preview_preflight.ts", {
    cwd: miniappRoot,
    stdio: "inherit",
    encoding: "utf8",
  });
} catch {
  process.exit(1);
}
