import pytest
import uuid
from httpx import AsyncClient


class TestNotes:
    async def test_create_note(self, client: AsyncClient, auth_headers1, team1):
        response = await client.post(
            f"/v1/teams/{team1.id}/notes",
            json={"title": "Test Note", "body": "Test body"},
            headers=auth_headers1
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Note"
        assert data["body"] == "Test body"
        assert data["version"] == "1"
        assert data["team_id"] == str(team1.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_note_unauthorized(self, client: AsyncClient, team1):
        response = await client.post(
            f"/v1/teams/{team1.id}/notes",
            json={"title": "Test Note", "body": "Test body"}
        )
        assert response.status_code == 401

    async def test_create_note_not_member(self, client: AsyncClient, auth_headers2, team1):
        response = await client.post(
            f"/v1/teams/{team1.id}/notes",
            json={"title": "Test Note", "body": "Test body"},
            headers=auth_headers2
        )
        assert response.status_code == 403

    async def test_create_note_empty_title(self, client: AsyncClient, auth_headers1, team1):
        response = await client.post(
            f"/v1/teams/{team1.id}/notes",
            json={"title": "", "body": "Test body"},
            headers=auth_headers1
        )
        assert response.status_code == 422

    async def test_list_notes(self, client: AsyncClient, auth_headers1, team1, user1, db_session):
        from app.models import Note
        note1 = Note(team_id=team1.id, author_id=user1.id, title="Note 1", body="Body 1", version="1")
        note2 = Note(team_id=team1.id, author_id=user1.id, title="Note 2", body="Body 2", version="1")
        db_session.add_all([note1, note2])
        await db_session.commit()

        response = await client.get(f"/v1/teams/{team1.id}/notes?limit=1", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notes"]) == 1
        assert data["next_cursor"] is not None

    async def test_list_notes_pagination(self, client: AsyncClient, auth_headers1, team1, user1, db_session):
        from app.models import Note
        from datetime import datetime, timedelta
        base_time = datetime.utcnow()
        for i in range(5):
            note = Note(
                team_id=team1.id,
                author_id=user1.id,
                title=f"Note {i}",
                body=f"Body {i}",
                version="1",
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i)
            )
            db_session.add(note)
        await db_session.commit()

        response = await client.get(f"/v1/teams/{team1.id}/notes?limit=2", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notes"]) == 2
        assert data["next_cursor"] is not None

        response = await client.get(f"/v1/teams/{team1.id}/notes?limit=2&cursor={data['next_cursor']}", headers=auth_headers1)
        assert response.status_code == 200
        data2 = response.json()
        assert len(data2["notes"]) == 2

    async def test_list_notes_not_member(self, client: AsyncClient, auth_headers2, team1):
        response = await client.get(f"/v1/teams/{team1.id}/notes", headers=auth_headers2)
        assert response.status_code == 403

    async def test_get_note(self, client: AsyncClient, auth_headers1, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="Test Note", body="Test body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.get(f"/v1/teams/{team1.id}/notes/{note.id}", headers=auth_headers1)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(note.id)
        assert data["title"] == "Test Note"
        assert data["body"] == "Test body"

    async def test_get_note_not_found(self, client: AsyncClient, auth_headers1, team1):
        fake_id = uuid.uuid4()
        response = await client.get(f"/v1/teams/{team1.id}/notes/{fake_id}", headers=auth_headers1)
        assert response.status_code == 404

    async def test_get_note_not_member(self, client: AsyncClient, auth_headers2, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="Test Note", body="Test body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.get(f"/v1/teams/{team1.id}/notes/{note.id}", headers=auth_headers2)
        assert response.status_code == 403

    async def test_update_note(self, client: AsyncClient, auth_headers1, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="Original", body="Original body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.patch(
            f"/v1/teams/{team1.id}/notes/{note.id}",
            json={"title": "Updated", "body": "Updated body", "version": "1"},
            headers=auth_headers1
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["body"] == "Updated body"
        assert data["version"] == "2"

    async def test_update_note_version_conflict(self, client: AsyncClient, auth_headers1, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="Original", body="Original body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.patch(
            f"/v1/teams/{team1.id}/notes/{note.id}",
            json={"title": "Updated", "version": "999"},
            headers=auth_headers1
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Version conflict: note has been modified"

    async def test_update_note_not_member(self, client: AsyncClient, auth_headers2, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="Original", body="Original body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.patch(
            f"/v1/teams/{team1.id}/notes/{note.id}",
            json={"title": "Updated", "version": "1"},
            headers=auth_headers2
        )
        assert response.status_code == 403

    async def test_delete_note(self, client: AsyncClient, auth_headers1, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="To Delete", body="Body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.delete(f"/v1/teams/{team1.id}/notes/{note.id}", headers=auth_headers1)
        assert response.status_code == 204

        response = await client.get(f"/v1/teams/{team1.id}/notes/{note.id}", headers=auth_headers1)
        assert response.status_code == 404

    async def test_delete_note_not_member(self, client: AsyncClient, auth_headers2, team1, user1, db_session):
        from app.models import Note
        note = Note(team_id=team1.id, author_id=user1.id, title="To Delete", body="Body", version="1")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.delete(f"/v1/teams/{team1.id}/notes/{note.id}", headers=auth_headers2)
        assert response.status_code == 403

    async def test_tenant_isolation(self, client: AsyncClient, auth_headers1, auth_headers2, team1, team2, user1, user2, db_session):
        from app.models import Note
        note1 = Note(team_id=team1.id, author_id=user1.id, title="Team 1 Note", body="Body", version="1")
        note2 = Note(team_id=team2.id, author_id=user2.id, title="Team 2 Note", body="Body", version="1")
        db_session.add_all([note1, note2])
        await db_session.commit()

        response1 = await client.get(f"/v1/teams/{team1.id}/notes", headers=auth_headers1)
        assert response1.status_code == 200
        assert len(response1.json()["notes"]) == 1
        assert response1.json()["notes"][0]["title"] == "Team 1 Note"

        response2 = await client.get(f"/v1/teams/{team2.id}/notes", headers=auth_headers2)
        assert response2.status_code == 200
        assert len(response2.json()["notes"]) == 1
        assert response2.json()["notes"][0]["title"] == "Team 2 Note"

        response_cross = await client.get(f"/v1/teams/{team2.id}/notes", headers=auth_headers1)
        assert response_cross.status_code == 403