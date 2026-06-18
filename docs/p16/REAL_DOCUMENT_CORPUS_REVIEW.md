# Real Document Corpus Review & Business Reality

## Business Reality Review

If Chen Kui receives 100 Add-Car requests, the realistic distribution of document types is:

- **Purchase Agreement / Buyer's Order:** 45% (Most common for new/used dealer purchases)
- **Window Sticker:** 15% (Often sent by dealer while customer is on the lot)
- **Registration (Temp/DMV):** 20% (Common for private party sales or existing owned cars)
- **Insurance Card:** 5% (Usually for transferring from another carrier)
- **WeChat Screenshot / VIN Photo:** 15% (Informal, messy, quick requests)

*Note: We are optimizing for the 80% (Contracts, Stickers, Registrations) while ensuring the system doesn't crash on the messy 15% (WeChat).*

## Final Recommendation

**1. What are the top 3 document types we must support before pilot?**
1. Purchase Agreements / Buyer's Orders
2. Window Stickers
3. DMV / Temporary Registrations

**2. What are the top 3 document types we can ignore for now?**
1. Driver Licenses (Not strictly necessary for the car itself, often handled separately)
2. Complex multi-car commercial schedules
3. Smog check certificates

**3. What document types create the highest OCR risk?**
- WeChat Screenshots (Mixed language, unstructured, fragmented)
- Trade-in Purchase Agreements (High risk of extracting the old car's VIN instead of the new one)
- Blurry/Glare VIN Dashboard Photos

**4. What document types create the highest commercial value?**
- Purchase Agreements (They contain almost 100% of the required Trusted Packet fields, including the elusive Lienholder info, saving the most broker time).

**5. What is the minimum corpus size required before running Chen Kui pilot?**
- 20 diverse documents (10 Contracts, 5 Stickers, 5 Registrations/Messy items) running through the OCR Kill Test Matrix with a >90% success rate on VIN and YMM extraction.

**6. Is current Trust Layer ready for real-document testing?**
- Yes. The architecture (Gemini Flash 2.5) is defined, the field contract is frozen, and the success criteria are clear. We must run the `P16_OCR_KILL_TEST_MATRIX_V2` against the `test_data/p16_real_docs/` corpus before the first live Chen Kui case.
