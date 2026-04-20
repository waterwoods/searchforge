/**
 * Add-Car record rail — Chinese labels for structured field ids.
 * Source of truth: configs/common/add_car_stage1_field_contract.json (labels_zh).
 */
import addCarStage1Contract from '../../contracts/add_car_stage1_field_contract.json';

const ADD_CAR_LABELS_ZH = addCarStage1Contract.labels_zh as Record<string, string>;

/** @deprecated use contract JSON — kept for callers that imported the map */
export const ADD_CAR_RAIL_FIELD_LABELS_ZH: Record<string, string> = ADD_CAR_LABELS_ZH;

export function railFieldLabel(field: string): string {
    return ADD_CAR_LABELS_ZH[field] ?? field.replace(/_/g, ' ');
}

const VEHICLE_IDS = new Set(['year', 'make_model', 'model', 'zip', 'delivery_date', 'vin']);
const DRIVER_IDS = new Set(['primary_driver']);
const CONTACT_IDS = new Set(['name', 'phone']);

function isMaterialsField(f: string): boolean {
    return /customer_says_sent|already_sent|already_sent_claimed|declaration|garaging|driver_license|questionnaire|registration|vin_photo|dec_page|screenshot|requested_|verify_carrier|notice_present|payment_proof/i.test(
        f,
    );
}

export type FieldGroup = { title: string; keys: string[] };

/** Group collected (or still-needed) field ids for scannable record summary */
export function groupAddCarRailFields(fieldIds: string[]): FieldGroup[] {
    const vehicle: string[] = [];
    const driver: string[] = [];
    const contact: string[] = [];
    const materials: string[] = [];
    const other: string[] = [];
    for (const f of fieldIds) {
        if (!f) continue;
        if (VEHICLE_IDS.has(f)) vehicle.push(f);
        else if (DRIVER_IDS.has(f)) driver.push(f);
        else if (CONTACT_IDS.has(f)) contact.push(f);
        else if (isMaterialsField(f)) materials.push(f);
        else other.push(f);
    }
    const out: FieldGroup[] = [];
    if (vehicle.length) out.push({ title: '车辆与提车', keys: vehicle });
    if (driver.length) out.push({ title: '驾驶人', keys: driver });
    if (contact.length) out.push({ title: '联系信息', keys: contact });
    if (materials.length) out.push({ title: '材料与核实', keys: materials });
    if (other.length) out.push({ title: '其他要点', keys: other });
    return out;
}

export function newCollectedSincePrior(prev: string[] | undefined, next: string[] | undefined): string[] {
    const p = new Set(prev ?? []);
    return (next ?? []).filter((f) => f && !p.has(f));
}

/** Fields that left `still_needed` vs prior turn (factual set diff). */
export function clearedStillNeededSincePrior(prev: string[] | undefined, next: string[] | undefined): string[] {
    const n = new Set(next ?? []);
    return (prev ?? []).filter((f) => f && !n.has(f));
}

/** Fields newly present in `still_needed` vs prior turn. */
export function newStillNeededSincePrior(prev: string[] | undefined, next: string[] | undefined): string[] {
    const p = new Set(prev ?? []);
    return (next ?? []).filter((f) => f && !p.has(f));
}
