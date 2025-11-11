#!/usr/bin/env node
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import depcheckModule from '../ui/node_modules/depcheck/dist/index.js';

const depcheck = depcheckModule.default ?? depcheckModule;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uiDir = path.resolve(__dirname, '..', 'ui');

const result = await depcheck(uiDir, {
    ignoreMatches: [],
});

const missing = result?.missing ?? {};

if (Object.keys(missing).length > 0) {
    console.error('❌ Missing dependencies detected:');
    for (const [pkg, files] of Object.entries(missing)) {
        console.error(`  - ${pkg}:`);
        for (const file of files) {
            console.error(`      • ${file}`);
        }
    }
    process.exit(1);
}

console.log('✅ Dependency check passed');
process.exit(0);

