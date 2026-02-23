# Skatetrax Admin Tool

CLI for restoring, migrating, and importing Skatetrax data.  
Replaces the manual `newUser.py` -> `load_skeletor.py` -> `STLdb.py` workflow.

## Prerequisites

- Python 3 with the `skatetrax` package installed (`pip install -e .` from the project root)
- PostgreSQL database running and configured via environment variables:
  - `PGDB_HOST`, `PGDB_NAME`, `PGDB_USER`, `PGDB_PASSWORD`
- Tables already created (`python -m skatetrax.models.setup_db -c`)
- PyYAML and pandas installed (both are existing project dependencies)

## First-Time Setup

Before running any restore commands, you need to create `auth.yaml` files
from the provided samples. These files contain passwords and are **gitignored**
-- they will never be committed to the repository.

```bash
cd admin/fixtures/users/sparkles
cp auth.yaml.sample auth.yaml
# Edit auth.yaml -- set a real password, verify email
```

Repeat for each user:

```bash
cd admin/fixtures/users/inara
cp auth.yaml.sample auth.yaml
# Edit auth.yaml -- set a real password, verify email
```

The `auth.yaml.sample` files are committed to the repo and contain everything
except the password (which is set to `CHANGE_ME`). The only field you **must**
change is `password`. The `uSkaterUUID`, `aLogin`, and `aEmail` fields are
pre-filled with the correct values for each user.

> **Why not prompt for the password?** This tool is designed for repeatable
> database re-initialization during development. Prompting would break that
> workflow. In production, user creation would go through the web application,
> not this tool.

## Quick Start

```bash
cd admin

# Validate fixtures before touching the database
./admin.py validate sparkles

# Full disaster recovery (blank database -> fully populated)
./admin.py restore sparkles --all

# One-time MariaDB migration (old integer-ID CSV -> Postgres UUIDs)
./admin.py migrate sparkles --csv path/to/ash_t_ice_time.csv
```

You can also run from the project root:

```bash
python admin/admin.py restore sparkles --all
python admin/admin.py migrate sparkles --csv path/to/ash_t_ice_time.csv
```

## Commands

### `restore` -- Load YAML fixtures into the database

Reads YAML fixture files and inserts data in dependency order.

```bash
# Run all steps
./admin.py restore <username> --all

# Run specific steps (can combine multiple)
./admin.py restore <username> --step pooled --step auth --step profile
```

**Available steps** (listed in dependency order):

| Step | What it loads | Source file |
|------|--------------|-------------|
| `pooled` | Coaches, locations, clubs (shared reference data) | `fixtures/pooled/*.yaml` |
| `auth` | Login credentials (password hashed at load time) | `fixtures/users/<name>/auth.yaml` |
| `profile` | Skater profile (uSkaterConfig row) | `fixtures/users/<name>/profile.yaml` |
| `equipment` | Boots, blades, skate configs | `fixtures/users/<name>/equipment.yaml` |
| `memberships` | Clubs, memberships, punch cards, LTS classes | `fixtures/users/<name>/memberships.yaml` |
| `maintenance` | Blade sharpening / maintenance history | `fixtures/users/<name>/maintenance.yaml` |
| `sessions` | Bulk session data from CSV | `sessions/<name>/*.csv` |

The `--all` flag runs every step in the order shown above.

Before any database writes, `restore` runs a **pre-flight validation** that
checks every coach, location, and club UUID referenced in the user's fixture
files against `fixtures/pooled/`. If anything is missing, the restore aborts
with a clear list of what's unresolved.

The `pooled` step is smart about re-runs -- if pooled reference data is already
present in the database (more than just the `setup_db` defaults), it skips
entirely. This prevents duplicate-key noise when restoring a second user.

### `migrate` -- One-time MariaDB to Postgres migration

Reads an old MariaDB-exported CSV, translates integer IDs to Postgres UUIDs
using mapping files, and inserts the results into `ice_time`.

```bash
./admin.py migrate <username> --csv <path-to-csv>
```

Mapping files used:
- `migrations/shared_mappings.yaml` -- locations, coaches, session types (shared across all users)
- `migrations/<username>/user_mappings.yaml` -- user-specific IDs (skater UUID, skate configs)

This command is designed to run once per user during the MariaDB transition.
The `migrations/` directory can be archived or deleted once all users are migrated.

### `import-sessions` -- Bulk import new session data

Imports a CSV file directly into the `ice_time` table. The CSV must already
contain Postgres UUIDs (no ID translation is performed).

```bash
./admin.py import-sessions <username> path/to/sessions.csv
```

If the CSV contains an `ice_time_id` or `id` column, it is dropped
automatically (Postgres auto-increments the primary key).

### `import-maintenance` -- Bulk import maintenance records

Imports a CSV file into the `maintenance` table. If the CSV does not contain
a `uSkaterUUID` column, it is injected from the user's `auth.yaml`.

```bash
./admin.py import-maintenance <username> path/to/maintenance.csv
```

### `validate` -- Dry-run fixture check

Parses all YAML fixtures for a user and reports issues without touching
the database. Checks for missing required fields and broken FK references
(e.g., a skate config referencing a boot ID that doesn't exist in the
equipment file).

```bash
./admin.py validate <username>
```

## Directory Structure

```
admin/
├── admin.py                          # This tool
├── README.md                         # This file
│
├── fixtures/
│   ├── samples/                      # Sample/template files -- COMMITTED
│   │   ├── pooled/
│   │   │   ├── coaches.yaml          # Fake coaches with placeholder UUIDs
│   │   │   ├── clubs.yaml
│   │   │   └── locations.yaml
│   │   └── users/newskater/          # Template for a new user
│   │       ├── auth.yaml.sample
│   │       ├── profile.yaml
│   │       ├── equipment.yaml
│   │       ├── memberships.yaml
│   │       └── maintenance.yaml
│   │
│   ├── pooled/                       # Real shared data -- GITIGNORED (PII)
│   │   ├── clubs.yaml
│   │   ├── coaches.yaml
│   │   └── locations.yaml
│   └── users/                        # Real user data -- GITIGNORED (PII)
│       ├── sparkles/
│       │   ├── auth.yaml.sample      # Template -- committed
│       │   ├── auth.yaml             # Real credentials -- GITIGNORED
│       │   ├── profile.yaml          # GITIGNORED
│       │   ├── equipment.yaml        # GITIGNORED
│       │   ├── memberships.yaml      # GITIGNORED
│       │   └── maintenance.yaml      # GITIGNORED
│       └── inara/
│           └── (same structure)
│
├── migrations/                       # MariaDB -> Postgres (one-time, archivable)
│   ├── shared_mappings.yaml          # Int->UUID for locations, coaches, types
│   └── sparkles/
│       └── user_mappings.yaml        # Int->UUID for this user's IDs -- GITIGNORED
│
└── sessions/                         # Session CSVs -- GITIGNORED
    ├── samples/
    │   └── sessions.csv              # Example CSV with placeholder UUIDs -- COMMITTED
    ├── sparkles/
    └── inara/
```

> **What's committed vs. gitignored?** Only sample/template files and the admin
> tool itself are committed. Real fixture data (coaches with phone numbers,
> user profiles, session history, migration mappings) is gitignored because it
> contains PII. After cloning, copy the samples into the real directories and
> populate with actual data.

## Two Types of Users

### Legacy users (migrated from MariaDB)

Users like **sparkles** (Ashley) existed in the old MariaDB database with
integer IDs. Their workflow has three parts:

```bash
# 1. Restore profile, equipment, maintenance from YAML fixtures
#    (sessions.csv in sessions/sparkles/ will also be loaded if present)
./admin.py restore sparkles --all

# 2. Clear the auto-loaded sessions if you want a clean MariaDB migration
#    (only needed if sessions/ contains stale data from a previous export)

# 3. One-time migration of session data (integer IDs -> Postgres UUIDs)
./admin.py migrate sparkles --csv path/to/mariadb_ice_time.csv

# 4. Import any post-migration sessions (already in UUID format)
./admin.py import-sessions sparkles sessions/sparkles/post_migration.csv
```

The `migrate` command reads `migrations/shared_mappings.yaml` (locations,
coaches, types) and `migrations/sparkles/user_mappings.yaml` (user-specific
IDs) to translate old integers into UUIDs. Once migration is complete, the
`migrations/` directory can be archived -- future session imports use
`import-sessions` with native UUIDs.

### New-platform users (started on Postgres)

Users like **inara** were created after the migration. All their data already
uses Postgres UUIDs. They have no migration files and never need the `migrate`
command.

```bash
# Full re-init after a database wipe -- one command
./admin.py restore inara --all
```

This loads her YAML fixtures (auth, profile, equipment, memberships) and picks
up session CSVs from `sessions/inara/` automatically.

After the MariaDB transition is complete, **every user** follows the
new-platform pattern. The `migrate` command becomes irrelevant.

## Adding a New User

1. Create fixture and session directories:

```bash
mkdir -p fixtures/users/newskater
mkdir -p sessions/newskater        # optional, for session CSVs
```

2. Create the auth sample and your local auth file:

```bash
cat > fixtures/users/newskater/auth.yaml.sample << 'EOF'
# Auth credentials for newskater
# Copy this file to auth.yaml and set a real password.
# auth.yaml is gitignored -- never commit real passwords.

aLogin: "newskater"
password: "CHANGE_ME"
aEmail: "skater@example.com"
phone_number: "5551234567"
uSkaterUUID: "REPLACE_WITH_UUID"
EOF
```

Generate a UUID for the new user:

```bash
python -c "from uuid import uuid4; print(uuid4())"
```

Put the generated UUID in the sample file, then create the real auth file:

```bash
cp fixtures/users/newskater/auth.yaml.sample fixtures/users/newskater/auth.yaml
# Edit auth.yaml -- set the real password
```

3. Create `profile.yaml` with skater info (see `sparkles/profile.yaml` or
   `inara/profile.yaml` as templates).

4. Optionally create `equipment.yaml`, `memberships.yaml`, and `maintenance.yaml`.
   Only create files for data the user actually has -- a beginner using rental
   skates with no club membership only needs `auth.yaml`, `profile.yaml`, and
   `equipment.yaml`.

5. If the user has session data, place CSV files in `sessions/newskater/`.
   These must already contain Postgres UUIDs (not MariaDB integer IDs).

6. Run:

```bash
./admin.py validate newskater    # check for issues first
./admin.py restore newskater --all
```

The `pooled` step is safe to re-run -- it will skip locations, coaches, and
types that already exist in the database.

## Edge Case Handling

- **Invalid dates**: Rows with `0000-00-00` or unparseable dates (common in
  MariaDB exports) are logged to the console and skipped automatically.
- **Mixed users in a CSV**: If a CSV contains rows for multiple users (e.g.,
  a full `ice_time` table dump), the tool filters to only the target user's
  rows and logs how many rows belonged to other users.

## Notes

- **Fixture paths** (YAML, migration mappings) are always resolved relative
  to `admin.py`, so the tool works from any working directory.
- **CSV paths** (passed as arguments) are resolved relative to your current
  working directory, as with any CLI tool.
- **`auth.yaml` files are gitignored.** Only `auth.yaml.sample` files are
  committed. After cloning the repo, run `cp auth.yaml.sample auth.yaml` for
  each user and set real passwords before running `restore --step auth`.
- **The `uSkaterUUID`** in `auth.yaml` is the single source of truth for a
  user's identity. All other fixture files omit it -- the CLI injects it at
  load time to keep things DRY.
