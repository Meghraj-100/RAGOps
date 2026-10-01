"""CLI evaluation runner — usable from CI or command line.

Usage:
    python -m app.evaluation.cli --strategy vector-similarity
    python -m app.evaluation.cli --strategy hybrid-search --threshold 0.02

Exit codes:
    0 — evaluation passed
    1 — regression detected (delta exceeds threshold)
"""

import argparse
import asyncio
import sys

from app.core.config import get_settings


async def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument("--strategy", default="vector-similarity",
                        choices=["vector-similarity", "hybrid-search", "reranking", "multi-query"])
    parser.add_argument("--dataset", default="default")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=None,
                        help="Regression threshold (overrides EVAL_REGRESSION_THRESHOLD)")
    args = parser.parse_args()

    settings = get_settings()
    if args.threshold is not None:
        settings.eval_regression_threshold = args.threshold

    from app.db.database import get_session_factory
    from app.evaluation.engine import run_evaluation

    session_factory = get_session_factory()
    async with session_factory() as db:
        try:
            result = await run_evaluation(args.strategy, args.dataset, args.top_k, db)
            await db.commit()

            print(f"\n{'='*50}")
            print(f"Evaluation: {args.strategy}")
            print(f"Dataset:    {args.dataset}")
            print(f"Cases:      {result.total_cases}")
            print(f"{'='*50}")
            print(f"Hit@1:      {result.hit_at_1:.1%}")
            print(f"Hit@3:      {result.hit_at_3:.1%}")
            print(f"Hit@5:      {result.hit_at_5:.1%}")
            print(f"MRR:        {result.mrr:.4f}")
            print(f"Avg Lat:    {result.avg_latency_ms:.0f}ms")
            print(f"P50 Lat:    {result.p50_latency_ms:.0f}ms")
            print(f"P95 Lat:    {result.p95_latency_ms:.0f}ms")
            print(f"{'='*50}")

            if result.regression_detected:
                print("\n❌ REGRESSION DETECTED")
                sys.exit(1)
            else:
                print("\n✅ Evaluation passed")
                sys.exit(0)

        except Exception as e:
            print(f"\n❌ Evaluation failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
