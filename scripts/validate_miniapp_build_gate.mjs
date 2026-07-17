#!/usr/bin/env node
/**
 * P20 Mini Program Build Gate entry (repo root or miniapp/).
 * SSOT: docs/product/p20_product_north_star.md §K
 */
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.dirname(here);
const miniappRoot = path.join(repoRoot, "miniapp");

if (!existsSync(path.join(miniappRoot, "app.json"))) {
  console.error("Mini Program Build Gate FAILED: miniapp/ not found");
  process.exit(1);
}

try {
  execSync("node --import tsx scripts/build_gate.ts", {
    cwd: miniappRoot,
    stdio: "inherit",
    encoding: "utf8",
  });
} catch {
  process.exit(1);
}
