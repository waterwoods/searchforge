# Founder Verification Checklist — Client Identity Persistence Deploy

**Before manual trial on Vercel:**

## Quick Checks (2 min)

1. [ ] Open production frontend URL
2. [ ] Add `?client=demo_broker` to URL → office/team wording changes
3. [ ] Customer Entry: paste "我想联系客服" → handoff wording uses demo_broker language
4. [ ] Create case with `?client=chen_kui`, then open same case with `?client=demo_broker`, append "好的，收到" → reply draft uses chen_kui (not demo_broker)

## If Any Fails

- Check browser console for CORS/network errors
- Verify `VITE_API_BASE_URL` in Vercel points to correct Cloud Run URL
- Report blocker before running full trial

## Pass = Ready for Trial

All 4 checks pass → Andy can run broker-style manual trial.
