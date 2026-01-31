<!--
  ============================================================
  Sync Impact Report
  ============================================================
  Version change: 0.0.0 (template) → 1.0.0 (initial ratification)
  Bump rationale: MAJOR — first ratification of project
    principles from blank template.

  Modified principles:
    - [PRINCIPLE_1_NAME] → I. Static-First
    - [PRINCIPLE_2_NAME] → II. Content as Data
    - [PRINCIPLE_3_NAME] → III. Standards Compliance
    - [PRINCIPLE_4_NAME] → IV. Automation & Agentic Refresh
    - [PRINCIPLE_5_NAME] → V. Incremental & Non-Destructive

  Added sections:
    - Technology Constraints (replaces [SECTION_2_NAME])
    - Content Workflow (replaces [SECTION_3_NAME])

  Removed sections: None (all template slots filled).

  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ no update needed;
      "Constitution Check" gate is generic and will be populated
      per-feature from these principles.
    - .specify/templates/spec-template.md — ✅ no update needed;
      functional-requirements format is compatible.
    - .specify/templates/tasks-template.md — ✅ no update needed;
      phase structure accommodates static-site tasks.
    - .specify/templates/checklist-template.md — ✅ no update
      needed; category slots are feature-driven.
    - .specify/templates/agent-file-template.md — ✅ no update
      needed; technology section will auto-populate from plans.
    - .specify/templates/commands/*.md — N/A (directory does
      not exist).

  Follow-up TODOs: None.
  ============================================================
-->

# WAVES Lab Website Constitution

## Core Principles

### I. Static-First

Every page MUST be deliverable as a pre-built static asset.
Server-side rendering, client-side SPAs, and runtime
databases are prohibited unless a feature explicitly
justifies an exception through the Complexity Tracking
process in the implementation plan.

- The site MUST build with Jekyll and produce a complete
  static output that functions without JavaScript enabled.
- Third-party scripts (analytics, widgets) MUST load
  asynchronously and MUST NOT block page rendering.
- All navigation, content display, and core reading
  experiences MUST work with HTML and CSS alone.

**Rationale**: A static site ensures fast load times,
minimal hosting requirements, long-term archival stability,
and security by eliminating server-side attack surface.

### II. Content as Data

All repeating content — people, publications, projects,
posts — MUST be stored as structured data in Jekyll
collections or YAML data files, never hard-coded into
layouts or includes.

- Each content type MUST use a dedicated Jekyll collection
  (e.g., `_people`, `_publications`, `_projects`) or a
  YAML file in `_data/`.
- Front matter schemas for each collection MUST be
  documented and kept consistent across all entries.
- Adding or updating a content item MUST require editing
  only a single Markdown/YAML file — never a layout or
  include.

**Rationale**: Structured content enables CMS integrations
(CloudCannon, Forestry), agentic tooling, and bulk
operations. It separates content from presentation, making
refresh operations predictable and scriptable.

### III. Standards Compliance

The site MUST conform to current web standards and
accessibility guidelines to ensure broad compatibility and
long-term maintainability.

- Generated HTML MUST be valid per the W3C HTML5
  specification. Build-time or CI validation is encouraged.
- The site MUST meet WCAG 2.1 Level AA accessibility
  requirements, including semantic markup, alt text for
  images, sufficient color contrast, and keyboard
  navigation.
- CSS MUST avoid vendor-specific hacks for modern browsers.
  The Minimal Mistakes theme's SCSS pipeline is the
  canonical styling pathway.
- Structured data (Schema.org, OpenGraph, citation
  metadata) SHOULD be included for publications and people
  pages to improve discoverability.

**Rationale**: Standards compliance ensures the site works
across devices and assistive technologies, and protects
against browser-version churn.

### IV. Automation & Agentic Refresh

The site MUST be designed so that content updates can be
performed by automated tools, CMS platforms, and AI agents
without requiring manual layout or configuration changes.

- Content files MUST follow naming conventions that tools
  can parse programmatically (e.g.,
  `AuthorYear_ID.md` for publications,
  `lastname.md` for people).
- Front matter fields MUST use consistent keys and value
  formats across all items in a collection. Any schema
  change MUST be applied to every existing entry.
- CMS configuration files (`cloudcannon.config.yml`,
  `.forestry/`) MUST stay in sync with collection schemas.
  Adding a front matter field to a collection requires
  updating the corresponding CMS config.
- Automation scripts (in `.specify/scripts/` or equivalent)
  MUST be idempotent: running the same script twice
  produces the same result.

**Rationale**: The primary goal of this project is to make
content easy to refresh. Enforcing machine-readable
conventions lets agents and integrations create, update, and
validate content without human intervention in the common
case.

### V. Incremental & Non-Destructive

Changes to the site MUST be incremental and
non-destructive. No operation should require rebuilding
content from scratch or risk data loss.

- Adding a new collection item MUST NOT require modifying
  existing items, layouts, or configuration.
- Removing a person or publication MUST NOT break links on
  other pages. Cross-references SHOULD degrade gracefully
  (e.g., display the name without a link if the profile
  is removed).
- Theme upgrades (Minimal Mistakes) MUST be tested against
  the full site build before merging. Custom overrides in
  `_layouts/`, `_includes/`, or `_sass/` MUST be tracked
  and documented so they survive theme updates.
- Git history MUST be preserved. Force-pushes to the main
  branch are prohibited.

**Rationale**: An academic website accumulates years of
content. Incremental design prevents regressions and ensures
that routine updates — a new paper, a graduating student —
are low-risk operations.

## Technology Constraints

- **Static generator**: Jekyll (Ruby). Switching generators
  (Hugo, Eleventy, etc.) constitutes a MAJOR constitutional
  amendment.
- **Theme**: Minimal Mistakes (gem-based). Custom overrides
  are permitted in `_layouts/`, `_includes/`, and `_sass/`
  but MUST be minimized and documented.
- **Ruby version**: 3.1+ as specified in the Gemfile.
- **CMS integrations**: CloudCannon and Forestry
  configurations are maintained. New CMS integrations MUST
  NOT conflict with existing ones.
- **Image delivery**: Cloudinary CDN via
  `jekyll-cloudinary`. Images SHOULD use responsive
  variants; raw assets live in `assets/images/`.
- **Hosting**: Static file hosting (no server-side
  execution assumed). The build output MUST be
  self-contained.
- **Dependencies**: New Jekyll plugins MUST be added to the
  Gemfile and MUST NOT require runtime server processes.

## Content Workflow

- **People**: Add or edit a single file in `_people/`.
  Front matter MUST include: `author`, `avatar`, `excerpt`,
  `title`, `portfolio-item-category`, `portfolio-item-tag`,
  and `date`. The `avatar` path MUST point to an existing
  image in `assets/images/people/`.
- **Publications**: Add or edit a single file in
  `_publications/` using the naming convention
  `AuthorYear_ID.md`. Front matter MUST include citation
  metadata fields as established by existing entries.
- **Posts/News**: Add a dated file in `_posts/` following
  the `YYYY-MM-DD-slug.md` convention.
- **Pages**: Static pages in `_pages/` are edited directly.
  New pages MUST be added to `_data/navigation.yml` if
  they should appear in site navigation.
- **Review**: All content changes SHOULD be submitted via
  pull request or CMS staging preview before merging to
  the main branch.

## Governance

This constitution is the authoritative reference for
architectural and workflow decisions on the WAVES Lab
website. All feature specifications, implementation plans,
and code reviews MUST verify compliance with these
principles.

- **Amendments**: Any change to a Core Principle or
  Technology Constraint requires a documented proposal,
  review, and an updated version number before the change
  takes effect. Content Workflow updates that do not alter
  principles may be made as PATCH amendments.
- **Versioning**: This document follows semantic versioning:
  - MAJOR: Principle removed, redefined, or technology
    stack changed.
  - MINOR: New principle or section added, or existing
    guidance materially expanded.
  - PATCH: Wording clarifications, typo fixes, non-semantic
    refinements.
- **Compliance review**: Each implementation plan MUST
  include a "Constitution Check" section (see
  `plan-template.md`) verifying alignment with all five
  Core Principles before work begins.

**Version**: 1.0.0 | **Ratified**: 2026-01-29 | **Last Amended**: 2026-01-29
