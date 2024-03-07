- # Description
	- The backend typically consists of two main components:
		- Supabase
		- FastAPI
- # DB Schema for Knowles I
	- ## Tables
		- ### Organizations
			- id (PK) uuid
			- name text
			- domain text
			- created_at timestamptz
			- updated_at timestamptz
			- deleted_at timestamptz
		- ### Workspaces
			- id (PK) uuid
			- organization_id (FK) uuid
			- name text
			- created_at timestamptz
			- updated_at timestamptz
			- deleted_at timestamptz
		- ### WorkspaceRoles
			- id (PK) uuid
			- workspace_id (FK) uuid
			- user_id (FK) uuid
			- role text (owner, member)
			- created_at timestamptz
			- updated_at timestamptz
		- ### Calls
			- id (PK) uuid
			- workspace_id (FK) uuid
			- start_time timestamptz
			- end_time timestamptz
			- status text (initiated, in_progress, completed, failed)
			- created_at timestamptz
			- updated_at timestamptz
		- ### CallParticipants
			- id (PK) uuid
			- call_id (FK) uuid
			- user_id (FK) uuid
			- role text (host, participant)
			- created_at timestamptz
			- updated_at timestamptz
		- ### CallRecordings
			- id (PK) uuid
			- call_id (FK) uuid
			- recording_url text
			- duration_in_seconds float
			- storage_bucket text
			- storage_object_key text
			- metadata jsonb
			- created_at timestamptz
			- updated_at timestamptz
		- ### Conversations
			- id (PK) uuid
			- call_id (FK) uuid
			- transcript text
			- summary text
			- created_at timestamptz
			- updated_at timestamptz
		- ### Users
			- id (PK) uuid
			- workspace_id (FK) uuid
			- name text
			- email text
			- phone_number text
			- created_at timestamptz
			- updated_at timestamptz
			- deleted_at timestamptz
	- ## Relationships
		- An `Organization` can have many `Workspaces`.
		- A `Workspace` can have many `Calls` and `Users`.
		- `Users` are associated with `Workspaces` through `WorkspaceRoles`, defining their roles as either owner or member.
		- A `Call` can have multiple `CallParticipants`, including one or more hosts and participants.
		- A `Call` can have many `Conversations`.
		- A `Call` is associated with one `CallRecording`, which stores metadata and a reference to the recording in a Supabase Storage Bucket.
	- ## Mermaid Entity Relationship Diagrams
		- ```mermaid.js
			erDiagram
			ORGANIZATIONS {
				uuid id PK
				text name
				text domain
				timestamptz created_at
				timestamptz updated_at
				timestamptz deleted_at
			}
			WORKSPACES {
				uuid id PK
				uuid organization_id FK
				text name
				timestamptz created_at
				timestamptz updated_at
				timestamptz deleted_at
			}
			WORKSPACEROLES {
				uuid id PK
				uuid workspace_id FK
				uuid user_id FK
				text role
				timestamptz created_at
				timestamptz updated_at
			}
			CALLS {
				uuid id PK
				uuid workspace_id FK
				timestamptz start_time
				timestamptz end_time
				text status
				timestamptz created_at
				timestamptz updated_at
			}
			CALLPARTICIPANTS {
				uuid id PK
				uuid call_id FK
				uuid user_id FK
				text role
				timestamptz created_at
				timestamptz updated_at
			}
			CALLRECORDINGS {
				uuid id PK
				uuid call_id FK
				text recording_url
				float duration_in_seconds
				text storage_bucket
				text storage_object_key
				jsonb metadata
				timestamptz created_at
				timestamptz updated_at
			}
			CONVERSATIONS {
				uuid id PK
				uuid call_id FK
				text transcript
				text summary
				timestamptz created_at
				timestamptz updated_at
			}
			USERS {
				uuid id PK
				uuid workspace_id FK
				text name
				text email
				text phone_number
				timestamptz created_at
				timestamptz updated_at
				timestamptz deleted_at
			}

			ORGANIZATIONS ||--o{ WORKSPACES : "can have many"
			WORKSPACES ||--o{ CALLS : "can have many"
			WORKSPACES ||--o{ USERS : "can have many"
			WORKSPACES ||--o{ WORKSPACEROLES : "links"
			USERS ||--o{ WORKSPACEROLES : "have roles in"
			CALLS ||--o{ CALLPARTICIPANTS : "can have multiple"
			CALLS ||--o{ CONVERSATIONS : "can have many"
			CALLS ||--|{ CALLRECORDINGS : "is associated with one"
		```

			