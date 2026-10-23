import pytest
from httpx import AsyncClient


class TestTeams:
    async def test_create_team(self, client: AsyncClient, auth_headers1):
        response = await client.post("/v1/teams", json={"name": "New Team"}, headers=auth_headers1)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Team"
        assert "id" in data
        assert "created_at" in data

    async def test_create_team_unauthorized(self, client: AsyncClient):
        response = await client.post("/v1/teams", json={"name": "New Team"})
        assert response.status_code == 401

    async def test_create_team_empty_name(self, client: AsyncClient, auth_headers1):
        response = await client.post("/v1/teams", json={"name": ""}, headers=auth_headers1)
        assert response.status_code == 422

    async def test_list_teams(self, client: AsyncClient, auth_headers1, team1):
        response = await client.get("/v1/teams", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == team1.name

    async def test_list_teams_only_own(self, client: AsyncClient, auth_headers1, auth_headers2, team1, team2):
        response = await client.get("/v1/teams", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(team1.id)

    async def test_get_team(self, client: AsyncClient, auth_headers1, team1):
        response = await client.get(f"/v1/teams/{team1.id}", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(team1.id)
        assert data["name"] == team1.name

    async def test_get_team_not_member(self, client: AsyncClient, auth_headers2, team1):
        response = await client.get(f"/v1/teams/{team1.id}", headers=auth_headers2)
        assert response.status_code == 403

    async def test_get_team_not_found(self, client: AsyncClient, auth_headers1):
        import uuid
        fake_id = uuid.uuid4()
        response = await client.get(f"/v1/teams/{fake_id}", headers=auth_headers1)
        assert response.status_code == 404

    async def test_list_team_members(self, client: AsyncClient, auth_headers1, team1, user1):
        response = await client.get(f"/v1/teams/{team1.id}/members", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == str(user1.id)
        assert data[0]["role"] == "admin"

    async def test_list_team_members_not_member(self, client: AsyncClient, auth_headers2, team1):
        response = await client.get(f"/v1/teams/{team1.id}/members", headers=auth_headers2)
        assert response.status_code == 403