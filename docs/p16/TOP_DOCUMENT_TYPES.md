# Top Document Types for Add-Car Workflow

Ranked by frequency of submission by customers to California Chinese auto insurance brokers.

## 1. Purchase Agreement / Buyer's Order
- **Purpose:** Official dealer contract showing vehicle purchase details.
- **Typical fields present:** VIN, Year, Make, Model, Customer Name, Address, ZIP, Lienholder, Effective Date (Purchase Date).
- **OCR difficulty:** Medium (Often long, dense text, sometimes scanned or photographed at an angle).
- **Broker usefulness:** Very High (Contains almost all required fields, including lienholder).
- **Extraction priority:** P0

## 2. Window Sticker (Monroney Sticker)
- **Purpose:** Manufacturer sticker showing vehicle specs and MSRP.
- **Typical fields present:** VIN, Year, Make, Model.
- **OCR difficulty:** Low to Medium (Standardized layout but often photographed through glass with glare).
- **Broker usefulness:** High (Perfect for exact vehicle trim and VIN verification).
- **Extraction priority:** P0

## 3. Temporary Registration / DMV Registration
- **Purpose:** Proof of state registration.
- **Typical fields present:** VIN, Year, Make, Model, Customer Name, Address, ZIP, License Plate.
- **OCR difficulty:** Medium (Standardized but often crumpled, folded, or poorly lit photos).
- **Broker usefulness:** High (Strong proof of garaging address and vehicle identity).
- **Extraction priority:** P1

## 4. Insurance ID Card (Previous/Current)
- **Purpose:** Proof of existing or prior insurance.
- **Typical fields present:** VIN, Year, Make, Model, Customer Name, Effective Dates.
- **OCR difficulty:** Low (Usually clean digital PDF or clear wallet card).
- **Broker usefulness:** Medium (Good for VIN and Name, lacks lienholder and sometimes full address).
- **Extraction priority:** P1

## 5. WeChat Screenshot
- **Purpose:** Informal communication of details from dealer or customer.
- **Typical fields present:** VIN (text or partial photo), Customer Name, random details.
- **OCR difficulty:** High (Mixed Chinese/English, unstructured chat bubbles, truncated text).
- **Broker usefulness:** Medium (Often the only way customers send info, but requires piecing together).
- **Extraction priority:** P1

## 6. Dealer Email PDF
- **Purpose:** Forwarded email from dealer with vehicle details.
- **Typical fields present:** VIN, Year, Make, Model, Customer Name, Lienholder.
- **OCR difficulty:** Low (Native digital text).
- **Broker usefulness:** High (Clean data).
- **Extraction priority:** P1

## 7. VIN Photo (Dashboard / Door Jamb)
- **Purpose:** Direct photo of the vehicle's VIN plate.
- **Typical fields present:** VIN only (sometimes barcode).
- **OCR difficulty:** High (Glare, dust, weird angles, low contrast).
- **Broker usefulness:** Medium (Provides ground-truth VIN but nothing else).
- **Extraction priority:** P2

## 8. Driver License
- **Purpose:** Proof of identity and driving history.
- **Typical fields present:** Customer Name, Address, ZIP, DOB, License Number.
- **OCR difficulty:** Medium (Holograms, glare, microprint).
- **Broker usefulness:** High (Crucial for driver rating, though less about the car itself).
- **Extraction priority:** P2
