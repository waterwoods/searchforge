# QA Fast Lane — Operator Checklist

1. Pin Cloud QA to min=1 / max=1:
   `gcloud run services update fiqa-api-qa --region=us-west1 --project=optimal-disk-472305-e2 --min-instances=1 --max-instances=1`
2. Obtain exact `wx_*` session ID (DevTools: `wx.getStorageSync('mp_customer_session_id')`).
3. Open current QA Preview Workbench → select persona → click「一键准备演示」.
4. Copy the single compile path; delete old DevTools `dit=` compile modes.
5. Complete the physical-phone customer submission.
6. Run post-phase automation:
   `bash scripts/run_qa_fast_lane.sh --phase post --case-id <case_id> --frontend-origin <preview-origin>`
7. Expected final PASS: invite PASS · Broker path PASS · evidence under `docs/evidence/qa-fast-lane/<run_id>/` · GO.

Status: READY FOR FOUNDER QA · NOT YET READY TO FREEZE
