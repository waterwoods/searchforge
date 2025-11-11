export const serializePayload = (input) => {
    const seen = new WeakSet();

    const isReactEl = (v) => v && typeof v === 'object' && ('$typeof' in v || v.$$typeof);

    const toPlain = (v) => {
        if (v == null) return v;
        if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return v;
        if (Array.isArray(v)) return v.map(toPlain);
        if (isReactEl(v)) return undefined;
        if (typeof v === 'function') return undefined;
        if (typeof v === 'object') {
            if (seen.has(v)) return undefined;
            seen.add(v);
            const out = {};
            for (const [k, val] of Object.entries(v)) {
                const pv = toPlain(val);
                if (pv !== undefined) out[k] = pv;
            }
            return out;
        }
        return undefined;
    };

    return toPlain(input);
};

