# P16 Trusted Packet — Real Document Corpus V1

**Goal:** Provide a realistic OCR / Extraction test corpus for the Trust Layer Sprint to validate Customer Docs → Extraction → Trusted Packet → Broker before running real customer pilots.

## Corpus Components

1. **[Top Document Types](TOP_DOCUMENT_TYPES.md)**
   - Research and ranking of the most common documents received by California auto insurance brokers.

2. **[Document Index](DOC_INDEX.md)**
   - Inventory of the 25 sample documents located in `test_data/p16_real_docs/`.

3. **[Packet Coverage Matrix](PACKET_COVERAGE_MATRIX.md)**
   - Analysis of which Trusted Packet fields can be reliably extracted from each document type.

4. **[OCR Kill Test Matrix V2](P16_OCR_KILL_TEST_MATRIX_V2.md)**
   - 20 realistic stress tests designed to validate Gemini Flash 2.5 extraction accuracy and edge-case handling.

5. **[Corpus Review & Final Recommendation](REAL_DOCUMENT_CORPUS_REVIEW.md)**
   - Business reality check on document frequency and final recommendations before the Chen Kui pilot.

## Physical Corpus Location

All test files are stored in:
`test_data/p16_real_docs/`

*(Note: Actual files are placeholders/samples for the purpose of the OCR Kill Tests).*
