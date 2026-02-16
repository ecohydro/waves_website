#!/usr/bin/env python3
"""
People Profile Sync Tool - Feature 003

Extract people data from CV.numbers, sync to Jekyll profiles, enrich with web search.
"""

import argparse
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.logger import setup_logger, logger
from services.cv_parser import CVParserService


def cmd_extract(args):
    """
    Extract people from CV.numbers sheets.

    Implements User Story 1 (P1): Extract from all five sheets and merge duplicates.
    """
    logger.info("=" * 60)
    logger.info("EXTRACTING PEOPLE FROM CV.NUMBERS")
    logger.info("=" * 60)

    # Initialize parser
    parser = CVParserService(args.numbers_file)

    # Load CV.numbers file
    try:
        parser.load_cv_file()
    except Exception as e:
        logger.error(f"Failed to load CV.numbers file: {e}")
        return 1

    # Parse all sheets
    logger.info("Parsing all sheets...")
    cv_sheets = parser.parse_all_sheets()

    # Display sheet-by-sheet summary
    logger.info("\nSheet Summary:")
    logger.info("-" * 60)
    total_entries = 0
    for sheet_name in CVParserService.SHEET_NAMES:
        cv_sheet = cv_sheets.get(sheet_name)
        if cv_sheet:
            entry_count = len(cv_sheet.entries)
            total_entries += entry_count
            logger.info(f"  ✓ {sheet_name}: {entry_count} entries")
        else:
            logger.info(f"  ✗ {sheet_name}: Not found or skipped")

    logger.info("-" * 60)
    logger.info(f"Total entries extracted: {total_entries}")

    # Merge duplicates
    logger.info("\nMerging duplicate entries...")
    people = parser.merge_duplicates()

    # Find merged entries
    merged_count = total_entries - len(people)
    if merged_count > 0:
        logger.info(f"\nMerged {merged_count} duplicate entries:")
        # Find people with multiple roles
        for person in people:
            if len(person.roles) > 1:
                role_types = [r.type for r in person.roles]
                logger.info(f"  - {person.name} ({' + '.join(role_types)})")

    # Display final summary
    logger.info("\n" + "=" * 60)
    logger.info(f"EXTRACTION COMPLETE: {len(people)} unique people")
    logger.info("=" * 60)

    # Verbose output: show all people
    if args.verbose:
        logger.info("\nDetailed People List:")
        logger.info("-" * 60)
        for person in sorted(people, key=lambda p: p.lastname):
            years_str = ""
            if person.years_active[0]:
                end_year = person.years_active[1] or "present"
                years_str = f" ({person.years_active[0]}-{end_year})"

            roles_str = ", ".join([r.type for r in person.roles])
            logger.info(f"  {person.name}{years_str}")
            logger.info(f"    Roles: {roles_str}")
            if person.research_interests:
                logger.info(f"    Research: {', '.join(person.research_interests[:2])}")
            logger.info("")

    if args.dry_run:
        logger.info("\n[DRY RUN] No files were modified")

    return 0


def cmd_sync(args):
    """
    Sync extracted people to profile files.

    Implements User Story 2 (P2): Match to existing profiles, update CV-sourced fields,
    preserve manual content, create new profiles.
    """
    logger.info("=" * 60)
    logger.info("SYNCING PEOPLE TO PROFILE FILES")
    logger.info("=" * 60)

    # Import services
    from services.profile_matcher import ProfileMatcherService
    from services.profile_sync import ProfileSyncService

    # First, we need to extract people from CV.numbers
    # (User must run extract first, or we run it here)
    logger.info("Step 1: Extracting people from CV.numbers...")

    parser = CVParserService(
        os.path.expanduser(
            '~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers'
        )
    )

    try:
        parser.load_cv_file()
        parser.parse_all_sheets()
        people = parser.merge_duplicates()
        logger.info(f"  Extracted {len(people)} unique people")
    except Exception as e:
        logger.error(f"Failed to extract people: {e}")
        return 1

    # Initialize services
    logger.info(f"\nStep 2: Loading existing profiles from {args.people_dir}...")
    matcher = ProfileMatcherService(args.people_dir)

    logger.info(f"\nStep 3: Matching people to profiles...")
    sync_service = ProfileSyncService(args.people_dir)

    # Match and sync each person
    matched_count = 0
    created_count = 0

    for person in people:
        # Find match
        match = matcher.find_match(person)

        # Log match result
        if match.is_match():
            matched_count += 1
            if args.verbose:
                logger.info(f"  ✓ {person.name} → {os.path.basename(match.profile_file.file_path)} "
                           f"({match.match_type}, confidence: {match.confidence:.2f})")
        else:
            created_count += 1
            if args.verbose:
                logger.info(f"  + {person.name} (will create new profile)")

        # Sync person
        try:
            sync_service.sync_person(person, match, dry_run=args.dry_run)
        except Exception as e:
            logger.error(f"Failed to sync {person.name}: {e}")
            continue

    # Display summary
    summary = sync_service.get_summary()

    logger.info("\n" + "=" * 60)
    logger.info("SYNC COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Matched to existing files: {matched_count}")
    logger.info(f"  Files updated: {summary['files_updated']}")
    logger.info(f"  Files created: {summary['files_created']}")
    logger.info(f"  Conflicts logged: {summary['conflicts_logged']}")
    logger.info("=" * 60)

    # Show conflicts if any
    if summary['conflicts_logged'] > 0:
        logger.info("\nConflicts (manual edits preserved):")
        for conflict in sync_service.conflicts_logged:
            logger.info(f"  ! {conflict['file']}: {conflict['field']}")
            logger.info(f"    CV value: {conflict['cv_value'][:50]}")
            logger.info(f"    Current value: {conflict['current_value'][:50]}")

    if args.dry_run:
        logger.info("\n[DRY RUN] No files were modified")

    return 0


def cmd_enrich(args):
    """
    Enrich profiles with web search data.

    Implements User Story 3 (P3): Search web for current information,
    present suggestions for manual review, apply approved suggestions.
    """
    logger.info("=" * 60)
    logger.info("ENRICHING PROFILES WITH WEB SEARCH")
    logger.info("=" * 60)

    # Import services
    from services.enrichment_service import EnrichmentService
    from models.enrichment import EnrichmentCache
    from models.profile_file import ProfileFile

    # Handle --clear-cache flag
    if args.clear_cache:
        cache = EnrichmentCache()
        if args.person:
            logger.info(f"Clearing cache for: {args.person}")
            cache.clear(args.person)
        else:
            logger.info("Clearing all cache...")
            cache.clear()
        logger.info("Cache cleared")
        return 0

    # Extract people from CV.numbers
    logger.info("Step 1: Extracting people from CV.numbers...")

    parser = CVParserService(
        os.path.expanduser(
            '~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers'
        )
    )

    try:
        parser.load_cv_file()
        parser.parse_all_sheets()
        people = parser.merge_duplicates()
        logger.info(f"  Extracted {len(people)} unique people")
    except Exception as e:
        logger.error(f"Failed to extract people: {e}")
        return 1

    # Filter to specific person if requested
    if args.person:
        people = [p for p in people if args.person.lower() in p.name.lower()]
        if not people:
            logger.error(f"Person not found: {args.person}")
            return 1
        logger.info(f"  Filtering to: {people[0].name}")

    # Initialize enrichment service
    logger.info("\nStep 2: Enriching profiles with web search...")
    enrichment_service = EnrichmentService()

    # Track statistics
    enriched_count = 0
    approved_count = 0
    declined_count = 0
    api_calls = 0

    # Enrich each person
    for person_idx, person in enumerate(people, start=1):
        logger.info(f"\n[{person_idx}/{len(people)}] {person.name}")
        logger.info("-" * 60)

        # Get suggestions
        suggestions = enrichment_service.enrich_person(
            person,
            force_refresh=args.force_refresh
        )

        if not suggestions:
            logger.info("  No suggestions found")
            continue

        # Group suggestions by field (take best suggestion per field)
        field_suggestions = {}
        for suggestion in suggestions:
            if suggestion.field not in field_suggestions or \
               suggestion.confidence > field_suggestions[suggestion.field].confidence:
                field_suggestions[suggestion.field] = suggestion

        # Present each suggestion for review
        for field, suggestion in field_suggestions.items():
            print(suggestion.format_for_review())

            # Interactive approval (skip if dry-run)
            if not args.dry_run:
                while True:
                    response = input("\n  Apply suggestion? [y/n/skip]: ").strip().lower()
                    if response in ['y', 'yes']:
                        # Apply suggestion
                        try:
                            # Load profile file
                            profile_path = suggestion.profile_file_path or \
                                          f"_people/{person.lastname.lower()}.md"

                            profile = ProfileFile(profile_path).load()

                            # Apply suggestion
                            suggestion.apply_to_profile(profile)
                            profile.save()

                            logger.info(f"  ✓ Applied: {field} = {suggestion.suggested_value}")
                            approved_count += 1
                            enriched_count += 1
                            break

                        except Exception as e:
                            logger.error(f"Failed to apply suggestion: {e}")
                            break

                    elif response in ['n', 'no']:
                        logger.info(f"  ✗ Declined: {field}")
                        declined_count += 1
                        break

                    elif response == 'skip':
                        logger.info(f"  ⊗ Skipped: {field}")
                        break

                    else:
                        print("  Invalid response. Please enter y, n, or skip.")

            else:
                # Dry-run mode: just show suggestion
                logger.info("  [DRY RUN] Suggestion shown above")

    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("ENRICHMENT COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  People processed: {len(people)}")
    logger.info(f"  Profiles enriched: {enriched_count}")
    logger.info(f"  Suggestions approved: {approved_count}")
    logger.info(f"  Suggestions declined: {declined_count}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("\n[DRY RUN] No files were modified")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="People Profile Sync Tool - Extract, sync, and enrich people profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract people from CV.numbers
  %(prog)s extract

  # Extract with verbose output
  %(prog)s extract --verbose

  # Extract from custom CV file location
  %(prog)s extract --numbers-file ~/path/to/CV.numbers

  # Sync extracted people to _people/ directory
  %(prog)s sync

  # Enrich profiles with web search
  %(prog)s enrich
        """
    )

    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    parser.add_argument(
        '--log-file',
        help='Path to log file (optional)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Extract subcommand
    extract_parser = subparsers.add_parser(
        'extract',
        help='Extract people from CV.numbers sheets'
    )
    extract_parser.add_argument(
        '-n', '--numbers-file',
        default=os.path.expanduser(
            '~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers'
        ),
        help='Path to CV.numbers file (default: ~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers)'
    )
    extract_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview mode: show what would be extracted without making changes'
    )

    # Sync subcommand
    sync_parser = subparsers.add_parser(
        'sync',
        help='Update people profile markdown files'
    )
    sync_parser.add_argument(
        '-p', '--people-dir',
        default='_people/',
        help='Directory containing people markdown files (default: _people/)'
    )
    sync_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview mode: show proposed changes without writing files'
    )

    # Enrich subcommand
    enrich_parser = subparsers.add_parser(
        'enrich',
        help='Enrich profiles with web search data'
    )
    enrich_parser.add_argument(
        '--person',
        help='Enrich specific person only (by name)'
    )
    enrich_parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force refresh: bypass cache and re-fetch from web'
    )
    enrich_parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear enrichment cache (all or specific person)'
    )
    enrich_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview mode: show suggestions without applying'
    )

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1

    # Validate inputs based on command
    if args.command == 'extract':
        # Validate numbers-file exists
        if not os.path.exists(args.numbers_file):
            logger.error(f"CV.numbers file not found: {args.numbers_file}")
            logger.info("Specify path with --numbers-file or ensure file exists at default location")
            return 1

    elif args.command == 'sync':
        # Validate people-dir exists
        if not os.path.exists(args.people_dir):
            logger.warning(f"People directory does not exist: {args.people_dir}")
            logger.info(f"Creating directory: {args.people_dir}")
            os.makedirs(args.people_dir, exist_ok=True)

    # Setup logging
    global logger
    logger = setup_logger(
        name='sync_people',
        log_file=args.log_file,
        verbose=args.verbose
    )

    # Execute command
    if args.command == 'extract':
        return cmd_extract(args)
    elif args.command == 'sync':
        return cmd_sync(args)
    elif args.command == 'enrich':
        return cmd_enrich(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
