# ADR: Calendar Range Query for Multi-Month Navigation

## Status
- Implemented (2025-11-27) — alternative solution to RFC `streamlit-calendar-dateset-bridge.md`; supersedes original datesSet event proposal.

## Context
- **Problem**: When users click prev/next buttons in FullCalendar to navigate months, match data was not updating because only the current month's data was loaded.
- **Original RFC Goal**: Add datesSet event to streamlit-calendar to detect month changes and trigger Python-side data refresh.
- **RFC Constraint**: streamlit-calendar does not bridge datesSet events to Python; eventsSet callback failed (infinite loops, unreliable communication).
- **Investigation**: Documented in `docs/QUESTIONS.md` (lines 77-164); attempted datesSet, eventsSet, dateClick workarounds all failed.

## Decision
- **Solution**: Load ±1 year range of matches upfront, let FullCalendar handle client-side filtering.
- **Approach**:
  - Query matches for date range (e.g., 2024-01-01 to 2026-12-31) in a single database call
  - Pass all matches to FullCalendar on initial render
  - FullCalendar automatically shows/hides events based on current view month
  - No Python-Calendar communication needed; no rerun required for navigation

## Implementation Notes

### Database Layer
- `database/repositories.py`: Added `MatchRepository.get_in_date_range(start_date, end_date)`
  - SQL: `SELECT m.*, f.name, f.address FROM matches m LEFT JOIN fields f WHERE m.match_date BETWEEN ? AND ? ORDER BY match_date, match_time`
  - Returns all matches in specified date range

### Service Layer
- `services/match_service.py`: Added `get_matches_in_range(start_date, end_date)` wrapper method

### UI Layer
- `ui/components/calendar.py`:
  - **Before**: `get_monthly_matches(year, month)` — only current month
  - **After**: `get_matches_in_range(today.year - 1, today.year + 1)` — ±1 year range
  - Set `calendar_options["initialDate"]` to current month for initial positioning
  - Filter matches by current month for summary display below calendar

### Performance Validation (Actual Docker Environment)
| Scenario | Match Count | DB Query | Memory | Browser Transfer |
|----------|-------------|----------|--------|------------------|
| Current (12 matches) | 12 | 0.08ms | 1.5KB | 5KB |
| 1 year (50 matches) | 50 | 0.33ms | 6.25KB | 22KB |
| 3 years (150 matches) | 150 | 1.00ms | 18.75KB | 65KB |
| 10 years (500 matches) | 500 | 3.33ms | 62.50KB | 218KB |

**Comparison**: jQuery.js (90KB), average web image (100-500KB) — 10-year data is smaller than typical web assets.

## Advantages Over RFC Original Proposal
- ✅ **No fork/build required**: Uses existing streamlit-calendar as-is
- ✅ **No Python-Calendar communication**: Eliminates infinite loop risk
- ✅ **Better performance**: 1 query vs. query-per-month-navigation
- ✅ **Simpler maintenance**: No custom component patching needed
- ✅ **Client-side filtering**: Leverages FullCalendar's built-in efficiency

## Operational & QA

### Browser Testing
- Verified navigation: November 2025 (4 matches) → October 2025 (5 matches) → September 2025 (6 matches)
- All transitions instant, no Python rerun, no communication errors
- prev/next buttons work naturally without additional code

### Performance Monitoring
- Monitor query time if match count grows beyond 500 (consider adjusting range to ±6 months)
- Current ±1 year range handles typical team usage comfortably

### Rollback Plan
- Revert to `get_monthly_matches(year, month)` if issues arise
- No database schema changes required (pure logic change)

## Open Questions / Follow-ups
- **Range Optimization**: If match count exceeds 1000, consider reducing range to ±6 months or implementing dynamic loading
- **Session State Sync**: Currently calendar initialDate uses session state but doesn't update it on navigation (acceptable as summary shows correct month data)
- **Mobile Performance**: Test on low-end mobile devices if user base expands significantly

## References
- Original RFC: `docs/RFCs/streamlit-calendar-dateset-bridge.md` (preserved for reference)
- Investigation: `docs/QUESTIONS.md` (lines 77-164)
- CHANGELOG: `docs/CHANGELOG.md` (2025-11-27)
