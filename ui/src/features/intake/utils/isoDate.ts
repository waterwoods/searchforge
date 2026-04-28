export function getIsoDateOffset(daysFromToday: number): string {
    const value = new Date();
    value.setHours(0, 0, 0, 0);
    value.setDate(value.getDate() + daysFromToday);
    return value.toISOString().slice(0, 10);
}
