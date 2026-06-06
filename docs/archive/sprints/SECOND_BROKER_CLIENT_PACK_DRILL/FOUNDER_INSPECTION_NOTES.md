# Founder Inspection Notes

Quick checks (15–20 minutes):

1. **Config load**  
   With API running: open Unified Intake with  
   `?client=socal_precision`  
   Confirm title **南加车险 · 客户入口** and quick-start **加车核价** / **转接人工**.

2. **Add-car happy path**  
   Paste a one-shot add-car message (year/model/zip/delivery/driver).  
   Expect handoff draft with **本所** + **营业日** language.

3. **Talk to agent**  
   Type **转接人工** (not only the button).  
   After this sprint, detection should fire; reply should match **socal_precision** handoff phrase.

4. **Known leak demo**  
   Send add-car + “材料发微信了” style message.  
   Observe whether reply still says **办公室** — if yes, that is the documented core leak, not a config mistake.

5. **Risk question**  
   Ask: “If we shipped `socal_precision` tomorrow, would *every* path sound like that office?”  
   Answer should be **no** until stitched strings are config-driven.
