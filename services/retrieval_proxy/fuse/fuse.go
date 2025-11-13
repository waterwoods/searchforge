package fuse

// mvp-5

import "sort"

// Item represents a ranked item returned by an upstream source.
type Item struct {
	ID      string
	Score   float64
	Payload any
}

// SourceResult represents the ordered results from a single source.
type SourceResult struct {
	Source string
	Items  []Item
}

// Contribution captures the contribution from a single source to the fused score.
type Contribution struct {
	Source   string
	Rank     int
	RawScore float64
	Weight   float64
}

// FusedItem represents a deduplicated result merged across sources.
type FusedItem struct {
	ID             string
	Score          float64
	Payload        any
	PrimarySource  string
	FirstRank      int
	Contributions  []Contribution
	OriginalScores map[string]float64
}

// CombineConfig controls how RRF aggregation selects top results.
type CombineConfig struct {
	RRFK       int
	TopKInit   int
	TopKMax    int
	ScoreFloor float64
}

// DefaultCombineConfig returns conservative defaults.
func DefaultCombineConfig() CombineConfig {
	return CombineConfig{
		RRFK:     60,
		TopKInit: 20,
		TopKMax:  64,
	}
}

// RRFCombine merges source results with Reciprocal Rank Fusion and deduplication.
func RRFCombine(results []SourceResult, cfg CombineConfig) []FusedItem {
	if cfg.RRFK <= 0 {
		cfg.RRFK = DefaultCombineConfig().RRFK
	}
	if cfg.TopKInit <= 0 {
		cfg.TopKInit = DefaultCombineConfig().TopKInit
	}
	if cfg.TopKMax <= 0 {
		cfg.TopKMax = DefaultCombineConfig().TopKMax
	}
	if cfg.TopKInit > cfg.TopKMax {
		cfg.TopKInit = cfg.TopKMax
	}

	type aggregate struct {
		item FusedItem
	}

	items := make(map[string]*aggregate)

	for _, src := range results {
		for idx, it := range src.Items {
			rank := idx + 1
			score := 1.0 / float64(cfg.RRFK+rank)

			agg, exists := items[it.ID]
			if !exists {
				agg = &aggregate{
					item: FusedItem{
						ID:            it.ID,
						Score:         0,
						Payload:       it.Payload,
						PrimarySource: src.Source,
						FirstRank:     rank,
						Contributions: []Contribution{},
						OriginalScores: map[string]float64{
							src.Source: it.Score,
						},
					},
				}
				items[it.ID] = agg
			} else {
				if agg.item.Payload == nil && it.Payload != nil {
					agg.item.Payload = it.Payload
				}
				if agg.item.OriginalScores == nil {
					agg.item.OriginalScores = make(map[string]float64)
				}
				if _, ok := agg.item.OriginalScores[src.Source]; !ok {
					agg.item.OriginalScores[src.Source] = it.Score
				}
			}

			agg.item.Score += score
			agg.item.Contributions = append(agg.item.Contributions, Contribution{
				Source:   src.Source,
				Rank:     rank,
				RawScore: it.Score,
				Weight:   score,
			})
		}
	}

	fused := make([]FusedItem, 0, len(items))
	for _, agg := range items {
		if cfg.ScoreFloor > 0 && agg.item.Score < cfg.ScoreFloor {
			continue
		}
		fused = append(fused, agg.item)
	}

	sortFused(fused)

	limit := cfg.TopKInit
	if limit > len(fused) {
		limit = len(fused)
	}
	if limit > cfg.TopKMax {
		limit = cfg.TopKMax
	}

	return fused[:limit]
}

func sortFused(items []FusedItem) {
	if len(items) <= 1 {
		return
	}
	sort.SliceStable(items, func(i, j int) bool {
		if items[i].Score == items[j].Score {
			return items[i].FirstRank < items[j].FirstRank
		}
		return items[i].Score > items[j].Score
	})
}


