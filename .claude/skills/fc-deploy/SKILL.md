---
name: fc-deploy
argument-hint: "[expected release, e.g. 1.0.0-2026.11.22]"
description: Family Campus – install the pushed release of my-family on the server named in its deploy.env. Checks first that my-family is committed and pushed and that the pushed image (<Family Campus version>-<content date>, ADR-0018) was built from exactly that commit and the Family Campus version in deploy.env, and whether the logins in the volume differ from the local data/campus.env (checksum only; applied after asking). If deploy.env names an old volume to migrate from, it copies it once (old volume kept as backup). Then pulls, restarts the container and verifies health, data and the public version. Use when the user says "install", "deploy" or starts /fc-deploy. Never commits, tags or pushes.
---

# fc-deploy – install the release of my-family

**Where:** Claude Code runs in the Family Campus folder. my-family is `my-family/` (or
`$FC_CAMPUS`, or the folder the user names); paths below such as `campus.json`,
`tiles/`, `deploy.env`, `material/` are relative to
it, `tools/…` and `sources/…` are Family Campus's. Git commands about my-family run
in my-family (`git -C my-family …`) and only if it is its own repository –
never put family data into Family Campus's git.

Starting this skill (or asking to install
the release) is the user's explicit request to deploy. It covers only the
steps below on the server; never commit, tag, push, build or change data
(except the one-time volume copy in 1b, after confirmation). Read
ADR-0005 and ADR-0018 of Family Campus.

**Arguments:** `$ARGUMENTS` – optional expected release `<version>-<date>`. If
given, it must be the tag of the image that `:latest` points to; otherwise stop
and ask.

**Values from `deploy.env`** (`set -a; . my-family/deploy.env; set +a`): `FC_HOST`
(ssh `-o BatchMode=yes`, commands with `sudo -n`), `FC_IMAGE`,
`FC_CONTAINER`, `FC_VOLUME` (mounted at `/data`), `FC_PORT`, `FC_PUBLIC_URL`;
optionally `FC_MIGRATE_FROM_VOLUME` and `FC_MIGRATE_FROM_CONTAINER`.
Below, `$REL` = `<FC_APP_VERSION>-<date of the content>` (the date of
my-family's HEAD commit, `git -C my-family log -1 --format=%cs` with `-` → `.`;
without a repository of its own: the tag the user names) and `$IMG` = `$FC_IMAGE:$REL`.

## 1. Check before deploying – stop and ask if anything does not match

Locally:

- if my-family is its own repository: `git -C my-family status --porcelain` empty,
  and `git -C my-family ls-remote` shows HEAD on the main branch (pushed);
- `FC_APP_VERSION` in `deploy.env` equals Family Campus's `VERSION`;
- the registry has the tag `$REL` (`/v2/<repo>/tags/list` of the registry in `FC_IMAGE`).

On the server (only pull and inspect):

- pull `:$REL` and `:latest`; both must be the same image id;
- labels: `family-campus.commit` = my-family's HEAD (short hash),
  `family-campus.content-date` = the date in `$REL`, `family-campus.app-version`
  starts with `FC_APP_VERSION`; `/srv/www/build.json` in the image has
  `"dev": false`.

If something does not match (uncommitted or unpushed work, `latest` ≠ `$REL`,
another commit, a test build): say exactly what and ask. Do not fix it by
committing or pushing.

### 1b. One-time migration of a volume (only if deploy.env asks for it)

If `FC_MIGRATE_FROM_VOLUME` is set, `$FC_VOLUME` does **not** exist yet and
the old volume does, the migration is due. Explain it and ask
(AskUserQuestion): "The live volume is copied once from
$FC_MIGRATE_FROM_VOLUME to $FC_VOLUME (short interruption, the old volume
stays as a backup). Run it now?" – options run / cancel. Only with run:

1. Before: row counts of `users`, `answers`, `attempts`, `review` in the old
   volume (read-only, `file:/data/campus.sqlite?mode=ro`, counts only) and
   the checksum of `/data/campus.env`.
2. `docker stop $FC_MIGRATE_FROM_CONTAINER` (no writes during the copy).
3. `docker volume create $FC_VOLUME`, then copy with ownership kept, the old
   volume mounted read-only:
   `docker run --rm --user root -v $FC_MIGRATE_FROM_VOLUME:/from:ro -v $FC_VOLUME:/to --entrypoint sh $IMG -c 'cp -a /from/. /to/'`
4. Compare: checksums of `campus.sqlite` (and `-wal`/`-shm` if present) and
   `campus.env` in both volumes must be equal.
5. Continue with step 2; after the checks in step 3 pass, remove the old
   container (`docker rm $FC_MIGRATE_FROM_CONTAINER`). **The old volume
   stays** as a backup – deleted only on a later explicit request, after a
   look at its content. Tell the user to remove the two `FC_MIGRATE_FROM_*`
   lines from `deploy.env`.

Rollback until the old container is removed: stop and remove the new
container, `docker start $FC_MIGRATE_FROM_CONTAINER`.

**Logins (`campus.env`)** – compare only checksums, never print the file:

```bash
sha256sum data/campus.env | cut -c1-64                       # local
ssh -o BatchMode=yes $FC_HOST "sudo -n docker run --rm --user root -v $FC_VOLUME:/data \
  --entrypoint sha256sum $IMG /data/campus.env" | cut -c1-64
```

If they differ, ask once (AskUserQuestion) whether to apply the local logins
(new passwords or people) with this deployment – options apply / not now.
Only with apply, write the file into the volume right before step 2 (the
file goes over ssh straight into the volume, nowhere else):

```bash
ssh -o BatchMode=yes $FC_HOST "sudo -n docker run --rm -i --user root -v $FC_VOLUME:/data \
  --entrypoint sh $IMG -c 'cat > /data/campus.env && chown campus:campus /data/campus.env && chmod 600 /data/campus.env'" < data/campus.env
```

Then compare the checksums again; they must match.

## 2. Deploy

```bash
sudo -n docker rm -f $FC_CONTAINER
sudo -n docker run -d --name $FC_CONTAINER --restart unless-stopped \
  --read-only --tmpfs /tmp -v $FC_VOLUME:/data \
  -p $FC_PORT:8080 $FC_IMAGE:latest
```

The URL path is built into the image. Never remove or recreate a volume
unless the user explicitly asks for it in the current request, and then look
at its content first.

## 3. Verify

- after ~35 s: `docker ps` shows `(healthy)`; the log line
  `Family Campus <FC_APP_VERSION> on :8080`;
- if logins were applied: the log lines `password changed: <name>` /
  `user created: <name>` (names only) and no `note: no password set`;
- data kept: row counts of `users`, `answers`, `attempts`, `review`
  (read-only, counts only) – after a migration they must equal the counts
  from 1b;
- publicly (`FC_PUBLIC_URL`): `api/version` shows the Family Campus version and
  the content date of `$REL` with `"dev": false`, `healthz`
  200, `manifest.webmanifest` 200, `config.json` 200, `api/history` 401
  (login still required).

## 4. Report (in the user's language)

What was checked, that the release `$REL` is live, that data was kept (counts),
whether a migration ran (old volume kept as backup) and that nobody has to
log in again – or, if logins were applied, who has a new password or was
added and must log in again (never the passwords).
