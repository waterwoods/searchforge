/**
 * P25 — DEV-only Vite middleware: write Golden Preview compile query into
 * gitignored miniapp/project.private.config.json (Founder laptop).
 */
import fs from 'node:fs';
import path from 'node:path';
import type { Plugin } from 'vite';

const ENTRY_PATH = 'pages/entry/entry';
const GOLDEN_NAME = 'pages/entry/entry (Golden QA session)';

export function goldenQaPreviewPlugin(repoRoot: string): Plugin {
    return {
        name: 'golden-qa-preview-prep',
        configureServer(server) {
            server.middlewares.use('/__qa__/prepare-golden-preview', (req, res, next) => {
                if (req.method !== 'POST') {
                    next();
                    return;
                }
                const chunks: Buffer[] = [];
                req.on('data', (c) => chunks.push(Buffer.from(c)));
                req.on('end', () => {
                    try {
                        const body = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}') as {
                            query?: string;
                        };
                        const query = String(body.query || '').trim();
                        if (!query.startsWith('token=h5t1.')) {
                            res.statusCode = 400;
                            res.setHeader('Content-Type', 'application/json');
                            res.end(JSON.stringify({ ok: false, error: 'invalid_query' }));
                            return;
                        }
                        const privatePath = path.join(repoRoot, 'miniapp', 'project.private.config.json');
                        let cfg: Record<string, unknown> = {
                            condition: { miniprogram: { list: [] } },
                        };
                        if (fs.existsSync(privatePath)) {
                            cfg = JSON.parse(fs.readFileSync(privatePath, 'utf8')) as Record<string, unknown>;
                        }
                        const condition = (cfg.condition as Record<string, unknown>) || {};
                        const mp = (condition.miniprogram as Record<string, unknown>) || {};
                        const list = Array.isArray(mp.list) ? (mp.list as Record<string, unknown>[]) : [];
                        let found = false;
                        for (const entry of list) {
                            if (String(entry.pathName || '') === ENTRY_PATH) {
                                entry.query = query;
                                entry.name = GOLDEN_NAME;
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            list.push({
                                name: GOLDEN_NAME,
                                pathName: ENTRY_PATH,
                                query,
                                launchMode: 'default',
                                scene: null,
                            });
                        }
                        mp.list = list;
                        condition.miniprogram = mp;
                        cfg.condition = condition;
                        fs.mkdirSync(path.dirname(privatePath), { recursive: true });
                        fs.writeFileSync(privatePath, `${JSON.stringify(cfg, null, 2)}\n`, 'utf8');
                        const linePath = path.join(
                            repoRoot,
                            'docs',
                            'evidence',
                            'golden_qa',
                            'last_reset',
                            'qa',
                            'devtools_compile_line.txt',
                        );
                        fs.mkdirSync(path.dirname(linePath), { recursive: true });
                        fs.writeFileSync(linePath, `${ENTRY_PATH}?${query}\n`, 'utf8');
                        res.statusCode = 200;
                        res.setHeader('Content-Type', 'application/json');
                        res.end(JSON.stringify({ ok: true, preview_prepared: true }));
                    } catch (err) {
                        res.statusCode = 500;
                        res.setHeader('Content-Type', 'application/json');
                        res.end(JSON.stringify({ ok: false, error: String(err) }));
                    }
                });
            });
        },
    };
}
