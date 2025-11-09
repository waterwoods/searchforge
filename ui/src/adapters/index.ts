/**
 * Adapters module - Export all adapters and types
 */

export {
    adaptMiniReport,
    fetchMiniReport,
    adaptLabOpsReport,
    fetchLabOpsReport,
    toStringSafe,
    type SafeMiniReport,
    type SafeLabOpsReport
} from './apiAdapters'

export type {
    LabMiniReportResponse
} from './types.generated'
