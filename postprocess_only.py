#!/usr/bin/env python3
"""
Re-run stage 4 (normalization) on an existing results folder, with no network.

Useful for experimenting with the core equation and the normalized score without
waiting for a full scan:

    python postprocess_only.py                       # newest Results folder
    python postprocess_only.py Results/Tase/2024...  # a specific one
    python postprocess_only.py --compare             # show where the two scores disagree
"""

import argparse
import glob
import os
import sys

import pandas as pd

import sss
import sss_config
import sss_post_processing


def newest_results_folder():
    hits = sorted(glob.glob("Results/*/*/sss_engine.csv"))
    if not hits:
        sys.exit("No Results/*/*/sss_engine.csv found. Run a scan first.")
    return os.path.dirname(hits[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", help="results folder containing sss_engine.csv")
    ap.add_argument("--compare", action="store_true",
                    help="report rank disagreement between sss_value and sss_value_normalized")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    folder = args.folder or newest_results_folder()
    print(f"Post-processing: {folder}")
    print(f"custom_sss_value_equation = {sss_config.custom_sss_value_equation}")

    num, den = sss.get_used_parameters_names_in_core_equation(sss_config.custom_sss_value_equation)
    print(f"  numerator   ({len(num)}): {', '.join(num)}")
    print(f"  denominator ({len(den)}): {', '.join(den)}")

    sss_post_processing.process_engine_csv(folder)
    out = os.path.join(folder, "sss_engine_normalized.csv")
    d = pd.read_csv(out)
    print(f"\nWrote {out}  ({len(d)} rows, {len(d.columns)} cols)")

    valid = d[(d["sss_value"] > 0) & (d["sss_value"] < sss.BAD_SSS)].copy()
    print(f"Valid rows (0 < sss_value < BAD_SSS): {len(valid)}")

    print(f"\nTop {args.top} by sss_value (multiplicative, lower is better):")
    print(valid.nsmallest(args.top, "sss_value")[
        ["Symbol", "Name", "sss_value", "sss_value_normalized"]].to_string(index=False))

    print(f"\nTop {args.top} by sss_value_normalized (additive, lower is better):")
    print(valid.nsmallest(args.top, "sss_value_normalized")[
        ["Symbol", "Name", "sss_value", "sss_value_normalized"]].to_string(index=False))

    if args.compare:
        valid["rank_mult"] = valid["sss_value"].rank()
        valid["rank_norm"] = valid["sss_value_normalized"].rank()
        rho = valid["rank_mult"].corr(valid["rank_norm"], method="spearman")
        valid["rank_gap"] = (valid["rank_mult"] - valid["rank_norm"]).abs()
        print(f"\nSpearman rank correlation between the two scores: {rho:.4f}")
        print(f"\nLargest {args.top} disagreements:")
        print(valid.nlargest(args.top, "rank_gap")[
            ["Symbol", "Name", "rank_mult", "rank_norm", "rank_gap"]].to_string(index=False))


if __name__ == "__main__":
    main()
