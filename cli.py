from __future__ import annotations

import argparse
import json
import logging

from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, ALevelScheme, StudentResult, SubjectGrade


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mwongozo Smart admission recommender")
    parser.add_argument("--pathway", default="a_level", choices=["a_level", "o_level", "equivalent"])
    parser.add_argument("--subjects", nargs="*", default=[])
    parser.add_argument("--combination", default=None)
    parser.add_argument("--regions", nargs="*", default=[])
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = build_parser().parse_args()
    student = StudentResult(
        pathway=AdmissionPathway(args.pathway),
        a_level_scheme=ALevelScheme.POST_2016,
        a_level_subjects=[
            SubjectGrade(subject=item.split("=", 1)[0], grade=item.split("=", 1)[1])
            for item in args.subjects
            if "=" in item
        ],
        combination=args.combination,
        preferred_regions=args.regions,
    )
    engine = RecommendationEngine()
    recommendations = engine.recommend(student)
    print(json.dumps([item.model_dump() for item in recommendations], indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

