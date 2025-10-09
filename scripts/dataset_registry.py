#!/usr/bin/env python3
"""
Dataset registry for multi-dataset golden bundle generation.
Returns configuration for each supported dataset.
"""

import pathlib

def get_dataset_registry():
    """Return dataset registry dictionary."""
    REG = {
        "scifact_ta": {
            "collection": "beir_scifact_full_ta",
            "vector_cfg": "configs/demo_beir_scifact_ta_vector.yaml",
            "hybrid_cfg": "configs/demo_beir_scifact_ta_hybrid.yaml",
            "queries_file": "data/scifact_queries.txt"
        },
        "fiqa": {
            "name": "fiqa",
            "collection": "beir_fiqa_full_ta",
            "beir_name": "fiqa",
            "split": "test",
            "paths": {
                "mode": "beir",
                "queries": "test",
                "qrels": "test"
            },
            "grid": {"candidate_k": [100, 200, 400], "rerank_k": [20, 50, 80]},
            "vector_cfg": "configs/demo_vector_fiqa.yaml",
            "hybrid_cfg": "configs/demo_hybrid_fiqa.yaml",
            "queries_file": "data/fiqa_queries.txt"
        }
    }
    return REG

def validate_dataset_files(dataset_name):
    """Validate that all required files exist for a dataset."""
    registry = get_dataset_registry()
    if dataset_name not in registry:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    config = registry[dataset_name]
    missing_files = []
    
    # Check config files
    for cfg_type in ["vector_cfg", "hybrid_cfg"]:
        cfg_path = pathlib.Path(config[cfg_type])
        if not cfg_path.exists():
            missing_files.append(f"{cfg_type}: {cfg_path}")
    
    # Check queries file
    queries_path = pathlib.Path(config["queries_file"])
    if not queries_path.exists():
        missing_files.append(f"queries_file: {queries_path}")
    
    if missing_files:
        print(f"Missing files for dataset '{dataset_name}':")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        dataset = sys.argv[1]
        try:
            valid = validate_dataset_files(dataset)
            if valid:
                print(f"Dataset '{dataset}' is valid")
            else:
                sys.exit(1)
        except ValueError as e:
            print(e)
            sys.exit(1)
    else:
        # Print all available datasets
        registry = get_dataset_registry()
        print("Available datasets:")
        for name, config in registry.items():
            print(f"  {name}: {config['collection']}")
