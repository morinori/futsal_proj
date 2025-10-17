# Personal Attendance Tab Player Selection UX Spec

## Context
- Page: `ui/pages/attendance.py`, `_render_personal_attendance_tab` renders the personal attendance workflow.
- Current behaviour: Streamlit `st.selectbox` defaults to the first player, so the page immediately loads that player's attendance view.
- Side effect: When staff open the tab and quickly record attendance, they often submit the first player's status unintentionally.
- Stakeholder input:
  1. Add a dummy top-level option.
  2. Ensure the dropdown has no active selection when the tab opens.

## Problem Statement
- Staff expect to explicitly choose a player before touching attendance controls. Auto-selecting the first player contradicts that expectation.
- Repeated mis-entries create data clean-up work and erode trust in the tool.
- We must make the “no player selected yet” state explicit, prevent accidental submissions, and keep the workflow fast for power users.

## Goals
- G1: Personal attendance tab opens with no player selected and with visible guidance to pick one.
- G2: Attendance buttons/actions stay disabled or hidden until a player is chosen.
- G3: Switching between tabs clears the personal player selection so the default is always blank when returning.
- G4: Provide a lightweight confirmation guard so users notice which player will be updated.

## Non-Goals
- NG1: Reworking the match-level attendance tab UX.
- NG2: Changing backend attendance rules or lock logic.
- NG3: Replacing the Streamlit component with a custom widget.

## UX / Flow Updates
1. **Initial state**
   - Render the “누구세요?” dropdown with a placeholder label such as `"선수를 선택하세요"` (`index=None`, `placeholder=...` in Streamlit ≥1.25).
   - Show helper text under the dropdown reminding users to pick a player before proceeding.
2. **Selection**
   - Once a player is selected, load the existing detail view unchanged.
   - Add a subtle status pill (e.g. `선택된 선수: 홍길동`) above the action buttons to reinforce the selected context.
3. **Action guard**
   - When the “출석 상태 변경” buttons are clicked, display a confirmation toast/modal summarising `{선수명} → {경기명}`. (Reuse the existing Streamlit `st.toast` or modal pattern already used elsewhere.)
4. **Tab transitions**
   - On entering the personal tab, reset `st.session_state["personal_attendance_player"]` if it points to a real player id.
   - When leaving the tab (detected on next render) the stored selection should be cleared so that reopening the tab shows the blank placeholder again.
5. **Fallback UX**
   - If Streamlit version does not support `index=None`, prepend a dummy option label (e.g. `"-- 선수를 선택하세요 --"`, id `None`) and block progression until a real player id is chosen.

## Functional Requirements
- **FR1**: Personal attendance tab must render without selecting any player; the dropdown value becomes `None` until the user picks a name.
- **FR2**: `AttendancePage._render_personal_attendance_tab` must gate all downstream calls behind `if selected_player_id is not None`.
- **FR3**: When the placeholder/dummy option is active, the detail panel and action buttons are hidden and a prompt is displayed.
- **FR4**: Session keys `personal_attendance_player`, `current_selected_player_*`, and `personal_match_select_*` are cleared when the placeholder is active.
- **FR5**: Attempting to submit attendance with no selected player must surface a user-facing warning instead of running service calls.
- **FR6**: Confirmation toast/modal must display the player name and match label before updating the attendance record.

## Technical Notes
- Verify Streamlit version (`requirements.txt`) to confirm support for `placeholder` and `index=None`. If unsupported, fallback to the dummy option pattern.
- Guard against residual state by clearing `st.session_state["personal_attendance_player"]` at the top of `_render_personal_attendance_tab` when `st.session_state.get("active_tab") != "personal"`. If tab tracking does not exist, introduce a simple `st.session_state["attendance_active_tab"]`.
- Ensure the dummy placeholder (if needed) is excluded from any downstream dictionaries to avoid key errors.
- Confirmation toast can reuse `st.toast` (Streamlit ≥ 1.25) or a lightweight `st.info` banner that clears after a short delay.
- Update unit or integration tests under `tests/` (create `tests/ui/test_attendance_personal.py` if none exist) to cover the no-selection guard logic.

## Acceptance Criteria
- AC1: Opening the personal tab shows a dropdown with placeholder text and no detail panel; no service calls for attendance data fire until a player is chosen.
- AC2: Selecting a player reveals their attendance data and the confirmation guard displays the correct player/match when updating.
- AC3: Returning to the tab after navigating elsewhere reverts the dropdown to the placeholder state.
- AC4: Attempting to interact with attendance actions without a valid player selection displays a warning and leaves data unchanged.

## QA / Testing
- Manual: Walk through tab entry → ensure no player is auto-selected → pick a player → update attendance → confirm toast appears.
- Regression: Switch between personal and match tabs repeatedly; ensure state resets and no stale selection persists.
- Automated: Add/expand tests to assert placeholder handling and state reset (mock `st.session_state`).

## Open Questions
- Do we need analytics logging to measure how often the placeholder prevents accidental submissions?
- Should the confirmation guard be opt-in for admins via settings?
- Does the placeholder text require localisation beyond Korean?
