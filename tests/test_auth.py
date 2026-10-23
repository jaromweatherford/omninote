import pytest
from httpx import AsyncClient


class TestAuth:
    async def test_register(self, client: AsyncClient):
        response = await client.post("/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "password123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert "id" in data
        assert "created_at" in data

    async def test_register_duplicate_email(self, client: AsyncClient, user1):
        response = await client.post("/v1/auth/register", json={
            "email": user1.email,
            "password": "password123"
        })
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post("/v1/auth/register", json={
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post("/v1/auth/register", json={
            "email": "test@test.com",
            "password": "short"
        })
        assert response.status_code == 422

    async def test_login(self, client: AsyncClient, user1):
        response = await client.post("/v1/auth/token", json={
            "email": user1.email,
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, user1):
        response = await client.post("/v1/auth/token", json={
            "email": user1.email,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/v1/auth/token", json={
            "email": "nonexistent@test.com",
            "password": "password123"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    async def test_me(self, client: AsyncClient, auth_headers1, user1):
        response = await client.get("/v1/auth/me", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user1.email
        assert data["id"] == str(user1.id)

    async def test_me_unauthorized(self, client: AsyncClient):
        response = await client.get("/v1/auth/me")
        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        response = await client.get("/v1/auth/me", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401