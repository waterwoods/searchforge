/**
 * Workbench drawer background refresh stability.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/utils/workbenchDrawerRefresh.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  resolveDrawerRefreshPresentation,
  shouldPreserveDrawerDetailDuringRefresh,
} from './workbenchDrawerRefresh';

{
  // Initial empty load may show skeleton; never treat background poll as initial load.
  const initialEmpty = resolveDrawerRefreshPresentation({
    hasDetail: false,
    initialLoading: true,
    backgroundRefreshing: false,
  });
  assert.equal(initialEmpty.showSkeleton, true);
  assert.equal(initialEmpty.showRefreshingBanner, true);
  assert.equal(initialEmpty.projectionLoading, true);

  const backgroundWithDetail = resolveDrawerRefreshPresentation({
    hasDetail: true,
    initialLoading: false,
    backgroundRefreshing: true,
  });
  assert.equal(backgroundWithDetail.showSkeleton, false);
  assert.equal(backgroundWithDetail.showRefreshingBanner, false);
  assert.equal(backgroundWithDetail.projectionLoading, false);

  // Even if a caller incorrectly pairs initialLoading with background, banner stays off
  // when detail is already present (stable surface).
  const stable = resolveDrawerRefreshPresentation({
    hasDetail: true,
    initialLoading: false,
    backgroundRefreshing: true,
  });
  assert.equal(stable.projectionLoading, false);
}

{
  assert.equal(
    shouldPreserveDrawerDetailDuringRefresh({
      selectedCaseId: 'case_a',
      incomingCaseId: 'case_a',
      backgroundRefreshing: true,
    }),
    true,
  );
  assert.equal(
    shouldPreserveDrawerDetailDuringRefresh({
      selectedCaseId: 'case_a',
      incomingCaseId: 'case_b',
      backgroundRefreshing: true,
    }),
    false,
  );
}

{
  // Source contract: background refresh must not flip detailLoading.
  const here = dirname(fileURLToPath(import.meta.url));
  const page = readFileSync(join(here, '../../../pages/DocumentIntakeInboxPage.tsx'), 'utf8');
  const refreshFn = page.slice(
    page.indexOf('const refreshDrawerCase = useCallback'),
    page.indexOf('const drawerLoadPresentation'),
  );
  assert.equal(refreshFn.includes('setDetailLoading(true)'), false);
  assert.match(page, /resolveDrawerRefreshPresentation/);
  assert.match(page, /key=\{`broker-detail-\$\{detail\.case_id\}`\}/);
  assert.match(page, /key=\{`intake-\$\{caseItem\.case_id\}`\}/);
}

{
  // Poll effect must not restart on refreshCase identity churn.
  const here = dirname(fileURLToPath(import.meta.url));
  const panel = readFileSync(
    join(here, '../components/MissingInformationChecklistPanel.tsx'),
    'utf8',
  );
  assert.match(panel, /refreshCaseRef/);
  assert.match(panel, /CUSTOMER_STATUS_POLL_MS/);
  const effectBlock = panel.slice(
    panel.indexOf('// While waiting for customer'),
    panel.indexOf('// Case change or safe server projection refresh'),
  );
  assert.equal(effectBlock.includes('refreshCase,'), false);
}

console.log('workbenchDrawerRefresh.test: PASS');
