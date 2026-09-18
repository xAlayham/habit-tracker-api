from datetime import date


def create_habit(client, headers, frequency="daily", name="Test Habit"):
    res = client.post("/habits", json={"name": name, "frequency": frequency}, headers=headers)
    assert res.status_code == 200
    return res.json()["id"]


def complete(client, headers, habit_id):
    res = client.patch(f"/habits/{habit_id}/complete", headers=headers)
    assert res.status_code == 200
    return res.json()


def test_complete_requires_auth(client, auth_headers):
    habit_id = create_habit(client, auth_headers)
    res = client.patch(f"/habits/{habit_id}/complete")
    assert res.status_code == 401


def test_complete_nonexistent_habit_returns_404(client, auth_headers):
    res = client.patch("/habits/99999/complete", headers=auth_headers)
    assert res.status_code == 404


def test_user_cannot_complete_other_users_habit(client, auth_headers, second_user_auth_headers):
    habit_id = create_habit(client, auth_headers)
    res = client.patch(f"/habits/{habit_id}/complete", headers=second_user_auth_headers)
    assert res.status_code == 403


def test_first_completion_starts_streak_at_one(client, auth_headers, freeze_date):
    freeze_date(date(2024, 1, 1))
    habit_id = create_habit(client, auth_headers)

    body = complete(client, auth_headers, habit_id)

    assert body["completed"] is True
    assert body["streak_count"] == 1
    assert body["last_completed_date"] == "2024-01-01"


def test_toggling_off_undoes_completion_and_decrements_streak(client, auth_headers, freeze_date):
    freeze_date(date(2024, 1, 1))
    habit_id = create_habit(client, auth_headers)

    complete(client, auth_headers, habit_id)          # complete -> streak 1
    body = complete(client, auth_headers, habit_id)    # toggle again same period -> undo

    assert body["completed"] is False
    assert body["streak_count"] == 0
    assert body["last_completed_date"] is None


def test_undo_never_takes_streak_below_zero(client, auth_headers, freeze_date):
    freeze_date(date(2024, 1, 1))
    habit_id = create_habit(client, auth_headers)

    complete(client, auth_headers, habit_id)  # streak 1
    complete(client, auth_headers, habit_id)  # undo -> streak 0
    body = complete(client, auth_headers, habit_id)  # complete again same day -> restarts at 1

    assert body["streak_count"] == 1


def test_consecutive_daily_completions_increment_streak(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="daily")

    freeze_date(date(2024, 1, 1))
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 1, 2))
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 2
    assert body["last_completed_date"] == "2024-01-02"


def test_gap_in_daily_completions_resets_streak(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="daily")

    freeze_date(date(2024, 1, 1))
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 1, 3))  # day 2 skipped
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 1


def test_weekly_streak_across_consecutive_iso_weeks(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="weekly")

    freeze_date(date(2024, 1, 1))  # ISO week 1 of 2024
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 1, 8))  # ISO week 2
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 2


def test_weekly_streak_resets_after_a_skipped_week(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="weekly")

    freeze_date(date(2024, 1, 1))  # ISO week 1
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 1, 22))  # ISO week 4, weeks 2-3 skipped
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 1


def test_monthly_streak_continues_across_a_year_boundary(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="monthly")

    freeze_date(date(2023, 12, 15))
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 1, 5))
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 2


def test_monthly_streak_resets_after_a_skipped_month(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="monthly")

    freeze_date(date(2024, 1, 5))
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 3, 5))  # february skipped
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 1


def test_yearly_streak_continues_in_consecutive_years(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="yearly")

    freeze_date(date(2023, 6, 1))
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 3, 1))
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 2


def test_yearly_streak_resets_after_a_skipped_year(client, auth_headers, freeze_date):
    habit_id = create_habit(client, auth_headers, frequency="yearly")

    freeze_date(date(2022, 6, 1))
    complete(client, auth_headers, habit_id)

    freeze_date(date(2024, 6, 1))  # 2023 skipped
    body = complete(client, auth_headers, habit_id)

    assert body["streak_count"] == 1


def test_undo_then_redo_restores_the_streak(client, auth_headers, freeze_date):
    """Regression test: undo used to wipe last_completed_date to None, so a
    follow-up completion couldn't tell it was continuing a streak and reset
    to 1 instead of restoring it."""
    habit_id = create_habit(client, auth_headers, frequency="daily")

    freeze_date(date(2024, 1, 1))
    complete(client, auth_headers, habit_id)  # streak 1

    freeze_date(date(2024, 1, 2))
    complete(client, auth_headers, habit_id)  # streak 2

    freeze_date(date(2024, 1, 3))
    body = complete(client, auth_headers, habit_id)  # streak 3
    assert body["streak_count"] == 3

    body = complete(client, auth_headers, habit_id)  # undo -> back to 2
    assert body["completed"] is False
    assert body["streak_count"] == 2
    assert body["last_completed_date"] == "2024-01-02"

    body = complete(client, auth_headers, habit_id)  # redo -> continues to 3, not reset to 1
    assert body["completed"] is True
    assert body["streak_count"] == 3
    assert body["last_completed_date"] == "2024-01-03"


def test_missed_days_report_zero_streak_without_touching_the_habit(client, auth_headers, freeze_date):
    """Regression test: streak_count on the stored habit only resets on the
    next completion, so a habit left untouched kept reporting its old streak
    forever. The displayed streak should read 0 once a period has been missed."""
    habit_id = create_habit(client, auth_headers, frequency="daily")

    freeze_date(date(2024, 1, 1))
    complete(client, auth_headers, habit_id)  # streak 1

    freeze_date(date(2024, 1, 2))
    complete(client, auth_headers, habit_id)  # streak 2

    # Still within the grace period (yesterday) -> streak still shown as alive.
    freeze_date(date(2024, 1, 3))
    res = client.get(f"/habits/{habit_id}", headers=auth_headers)
    assert res.json()["streak_count"] == 2

    # 19 days untouched -> long past the previous period, should read as 0.
    freeze_date(date(2024, 1, 21))
    res = client.get(f"/habits/{habit_id}", headers=auth_headers)
    body = res.json()

    assert body["completed"] is False
    assert body["streak_count"] == 0
    # the underlying record is untouched until the next completion
    assert body["last_completed_date"] == "2024-01-02"
