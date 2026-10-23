# Project Plan: Multi-Team Notes Service

## 1. Purpose
Build a runnable REST service where users can create and work with notes shared among small teams. Deliver the service, database migrations, tests, local development setup, and a README.

The project will grow in three phases:

1. **Phase 1**: Team-scoped notes with basic authentication.
2. **Phase 2**: Fine-grained permissions on teams and notes.
3. **Phase 3**: Real-time collaborative editing, so multiple users can edit the same note simultaneously and see one another's changes.

Each phase should leave the service usable. Later phases extend the earlier API and data model rather than replacing them wholesale.

## 2. Goals and Initial Scope
- Users can create, read, update, and delete notes.
- Notes belong to teams.
- Access checks prevent users from reading or changing resources they are not permitted to access.
- Concurrent edits eventually merge without silently overwriting one another.
- A reviewer can run the service locally, initialize its database, and run its tests from documented instructions.
- Initially, notes contain a title and plain-text body. Rich-text editing, attachments, comments, search, revision history, external identity providers, and invitation workflows are out of scope unless needed to support a later phase.

## 3. Proposed Technology and Architecture
- **Language**: Python
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Testing**: Pytest
- **Local Development**: Docker Compose

Organize the application around API handlers, authentication, persistence, and business logic. Put authorization rules behind a policy interface from Phase 1:

```
authorize(user, action, resource) -> allow or deny
```

- Phase 1 implements a simple membership rule; Phase 2 adds role-based grants.
- API handlers should call the same policy layer rather than implement their own access checks.
- Use REST for normal resource operations. Phase 3 adds a WebSocket endpoint for live editing.
- PostgreSQL remains the durable source of truth; the WebSocket is a delivery mechanism, not storage.

## 4. Core Data Model

### Phase 1
- **users**: ID, unique email, password hash, creation time.
- **teams**: ID, name, creation time.
- **memberships**: team ID, user ID, role; unique (team_id, user_id).
- **notes**: ID, team ID, author ID, title, body, version, creation and update times.

- Use UUID identifiers, foreign keys, and an index on (team_id, updated_at) for team note listings.
- Store passwords using a modern password-hashing algorithm, never as plaintext.

### Phase 2
- Add resource-level grants. A grant identifies a user or team principal and assigns a role on a team or note.
- This can use separate grant tables for teams and notes, or a common resource-grant table; choose based on the database constraints and query clarity established during implementation.

**Role Behavior and Inheritance:**
- **Reader**: may view the resource.
- **Writer**: may view and edit notes; on a team, may create notes.
- **Admin**: may perform writer actions and manage access. Define explicitly whether this includes deletion.
- **Inheritance**: note access includes access inherited from its team. Note-specific grants may add access. Do not introduce explicit deny rules in the initial version.
- A user may grant access only if authorized to manage access on that resource, and may not grant a role above their own.

### Phase 3
- Add durable collaborative document storage: a document snapshot per note and a log of accepted document updates.
- Updates need unique identifiers for idempotent retries.
- Define a safe snapshot-compaction process so old updates can be compacted without losing newer ones.

## 5. API Outline
Use a `/v1` prefix.

### Phase 1: Core REST API
- `POST /v1/auth/token` — authenticate and receive a bearer token.
- `GET /v1/me` — return the user and their team memberships.
- `GET /v1/teams/{team_id}/notes` — list notes with bounded pagination.
- `POST /v1/teams/{team_id}/notes` — create a note.
- `GET /v1/teams/{team_id}/notes/{note_id}` — retrieve a note.
- `PATCH /v1/teams/{team_id}/notes/{note_id}` — update note fields.
- `DELETE /v1/teams/{team_id}/notes/{note_id}` — delete a note.

- Use version checks for REST updates. Return 409 Conflict if the supplied version is stale, preventing silent overwrites.
- Use consistent JSON error responses and avoid revealing whether an inaccessible resource exists.

### Phase 2: Access Management
- Add endpoints to inspect and manage grants on teams and notes.
- A grant-management endpoint must enforce the caller's admin permissions, validate the principal and role, and prevent privilege escalation.
- Document whether a user's team membership is separate from resource access or is itself represented through grants; avoid having two conflicting sources of permission truth.

### Phase 3: Live Editing
- Add a WebSocket endpoint scoped to a specific note, for example:
  ```
  /v1/teams/{team_id}/notes/{note_id}/collaboration
  ```
- Authenticate and authorize the connection, synchronize document state, accept updates from writers and admins, and relay updates to other authorized connected users.
- Readers may receive updates but may not submit edits.
- Recheck access when permissions change and close connections that lose authorization.

## 6. Delivery Phases

### Phase 1 — Usable Team Notes Service
**Work:**
- Set up the application, PostgreSQL database, Docker Compose, configuration, and migrations.
- Implement user and team provisioning through a documented CLI or seed command.
- Implement authentication, team-scoped note CRUD, pagination, and the policy interface.
- Add REST version checks and consistent error handling.
- Write the README with setup, migration, sample-data, test, and API-doc instructions.

**Acceptance Criteria:**
- A reviewer can start the service locally using the README.
- An authenticated team member can perform permitted note operations.
- Unauthenticated users and users outside the team cannot access its notes.
- Updates with stale versions fail rather than overwrite newer content.
- Automated tests cover CRUD, validation, pagination, and tenant isolation.

### Phase 2 — Fine-Grained Permissions
**Work:**
- Add grants for users and teams on teams and notes.
- Implement role resolution, team-to-note inheritance, grant management, and authorization middleware/dependencies calling the policy service.
- Apply the same policy checks to every relevant REST operation.
- Define grant revocation behavior and ensure it takes effect immediately for REST requests.

**Acceptance Criteria:**
- Direct-user and team grants produce the expected access.
- Inherited team permissions apply to notes.
- Readers cannot write; writers cannot manage access; admins can manage access within their authority.
- Revoked users lose access.
- Tests cover cross-team grants, inheritance, role boundaries, and privilege escalation attempts.

### Phase 3 — Real-Time Collaborative Editing
**Work:**
- Run a technical spike to select and validate a maintained CRDT implementation and compatible client/server libraries.
- Limit the first collaborative document to the note body; retain ordinary REST updates for title and metadata.
- Add document snapshot and update persistence, idempotent update handling, and snapshot compaction.
- Implement WebSocket authentication, authorization, synchronization, update relay, reconnect recovery, payload limits, and connection cleanup after permission revocation.
- Integrate a client or test client that demonstrates concurrent editing.
- Roll out behind a feature flag, initially enabled only for test teams.

**Acceptance Criteria:**
- Two users can make overlapping edits and converge to the same content.
- Changes are visible to other connected editors promptly.
- Disconnecting and reconnecting restores missed changes.
- A service restart does not lose acknowledged changes.
- Readers cannot submit edits; revoked users stop receiving updates.
- Tests cover duplicate or reordered updates, persistence failure, reconnect, restart, compaction, and authorization.

## 7. Security and Operational Requirements
- Scope every note query and update by the authorized team/resource.
- Keep authorization rules centralized and testable.
- Use environment variables for secrets and provide placeholders only in `.env.example`.
- Bound pagination, WebSocket payload size, connection counts, and update rates.
- Avoid logging note bodies, authentication tokens, or raw collaboration updates.
- Add health checks and clear startup errors for missing or invalid configuration.
- Provide database migrations and a documented backup/restore approach before production use.

## 8. Key Risks and Tradeoffs
- **Authorization complexity**: Fine-grained grants can be hard to reason about. Explicit inheritance and role semantics, centralized policy checks, and focused tests reduce this risk.
- **Concurrent editing complexity**: CRDTs support concurrent changes but introduce client/server library choices, durable update logs, and compaction. Validate the approach in a spike before building the full feature.
- **Authentication lifecycle**: Short-lived bearer tokens are simple to start with but are not immediately revocable. Document that limitation; improve token revocation or adopt an identity provider if operational needs require it.
- **Migration compatibility**: Moving the note body into collaborative document storage can create two competing sources of truth. Define a migration and cutover strategy before enabling Phase 3.
- **Scope growth**: Search, rich text, offline editing, history, and sharing workflows can each expand the project significantly. Keep them out of the first delivery unless a concrete requirement justifies them.

## 9. Project Deliverables
- Runnable service and database setup.
- Versioned API and database migrations.
- Automated tests for each phase, especially authorization and concurrent-update behavior.
- README covering setup, configuration, migrations, sample users/teams, endpoints, tests, and known limitations.
- A short architecture note recording permission semantics, collaboration protocol decisions, and migration choices.