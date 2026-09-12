def test_create_habit_requires_auth(client):
    response = client.post("/habits", json={"name": "nap", "frequency": "daily"})
    assert response.status_code == 401

def test_create_habit_with_auth(client, auth_headers):
    habit_data = {"name": "Read at night", "frequency": "daily"}
    response = client.post("/habits", json=habit_data, headers=auth_headers)

    assert response.status_code == 200
    created_habit = response.json()
    assert created_habit["name"] == "Read at night"

    get_response = client.get("/habits", headers=auth_headers)

    assert get_response.status_code == 200
    habits_list = get_response.json()
    assert any(habit["id"] == created_habit["id"] for habit in habits_list)

def test_get_nonexistent_habit_returns_404(client, auth_headers):
    nonexistent_id = 99999
    response = client.get(f"/habits/{nonexistent_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Habit not found"

def test_user_cannot_get_or_delete_other_users_habit(client, auth_headers, second_user_auth_headers):

    habit_data = {"name": "User 1 Habit", "frequency": "daily"}
    create_res = client.post("/habits", json=habit_data, headers=auth_headers)
    habit_id = create_res.json()["id"]

    get_res = client.get(f"/habits/{habit_id}", headers=second_user_auth_headers)
    assert get_res.status_code == 403
    assert get_res.json()["detail"] == "Not authorized to access this habit"

    delete_res = client.delete(f"/habits/{habit_id}", headers=second_user_auth_headers)
    assert delete_res.status_code == 403
    assert delete_res.json()["detail"] == "Not authorized to access this habit"

def test_delete_own_habit_success(client, auth_headers):
    habit_data = {"name": "Drink Water", "frequency": "daily"}
    create_res = client.post("/habits", json=habit_data, headers=auth_headers)
    habit_id = create_res.json()["id"]

    delete_res = client.delete(f"/habits/{habit_id}", headers=auth_headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["message"] == "Habit successfully deleted"

    get_res = client.get(f"/habits/{habit_id}", headers=auth_headers)
    assert get_res.status_code == 404