import { z } from 'zod';

// Schema for Evidence (can be detailed later if needed)
const EvidenceSchema = z.object({
    file: z.string(),
    span: z.object({
        start: z.number(),
        end: z.number(),
    }),
    snippet: z.string(),
});

// Schema for Edge Evidence
const EdgeEvidenceSchema = z.object({
    file: z.string(),
    line: z.number(),
    context: z.string().optional().nullable(),
    signature: z.string().optional().nullable(),
});

// Schema for Metrics
const MetricsSchema = z.object({
    loc: z.number().optional().nullable(),
    complexity: z.number().optional().nullable(),
});

// Schema for a single Node
export const NodeSchema = z.object({
    id: z.string(),
    fqName: z.string(),
    kind: z.string(),
    language: z.string(),
    evidence: EvidenceSchema,
    signature: z.string().optional().nullable(),
    doc: z.string().optional().nullable(),
    metrics: MetricsSchema.optional().nullable(),
    hotness_score: z.number().optional().nullable(),
    data: z.record(z.string(), z.any()).optional().nullable(),
});

// Schema for a single Edge
export const EdgeSchema = z.object({
    from: z.string(), // Zod handles the 'from' keyword correctly
    to: z.string(),
    type: z.string(),
    evidence: EdgeEvidenceSchema.optional().nullable(),
});

// The main Data Contract for the entire graph payload
export const GraphDataSchema = z.object({
    nodes: z.array(NodeSchema),
    edges: z.array(EdgeSchema),
});

// We can also infer TypeScript types directly from our schemas
export type Node = z.infer<typeof NodeSchema>;
export type Edge = z.infer<typeof EdgeSchema>;
export type GraphData = z.infer<typeof GraphDataSchema>;

