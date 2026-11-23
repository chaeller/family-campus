# Operations

Commands run in the Family Campus folder; the scripts use `my-family/` (or the folder
given to them). Commands with `$FC_…` use my-family's `deploy.env`:
`set -a; . my-family/deploy.env; set +a`.

## The Docker image

my-family runs as one Docker image: it contains the server and `VERSION` of
Family Campus and the site built from Family Campus and my-family; the URL
path is built in. `tools/campus-image.sh` builds it locally (Docker needed):

```bash
tools/campus-image.sh --dev   # test build of the working trees → $FC_IMAGE:dev
tools/campus-image.sh         # release build → $FC_IMAGE:<version>-<content date> and :latest
```

One version (ADR-0018): a release image is tagged with the Family Campus
version and the date of my-family's content, e.g. `1.0.0-2026.11.22`. A
release build refuses a Family Campus checkout that is not clean or not at
`FC_APP_VERSION`, and – if my-family is its own git repository – uncommitted
changes in my-family. Labels record what it was built from:
`family-campus.app-version`, `family-campus.content-date` and
`family-campus.commit` (my-family). Test images say "test version" in the
footer and are never tagged `latest`.

The container runs as an unprivileged user with a read-only root file
system; all data is in the volume at `/data`.

## First start on a server

```bash
sudo docker volume create $FC_VOLUME
# logins: from your machine straight into the volume (the file is stored nowhere else)
ssh $FC_HOST "sudo docker run --rm -i --user root -v $FC_VOLUME:/data --entrypoint sh $FC_IMAGE \
  -c 'cat > /data/campus.env && chown campus:campus /data/campus.env && chmod 600 /data/campus.env'" < data/campus.env
```

## Start and update

```bash
sudo docker pull $FC_IMAGE
sudo docker rm -f $FC_CONTAINER 2>/dev/null
sudo docker run -d --name $FC_CONTAINER --restart unless-stopped \
  --read-only --tmpfs /tmp -v $FC_VOLUME:/data -p $FC_PORT:8080 $FC_IMAGE
```

The volume keeps logins and progress across updates. With Claude Code,
`/fc-deploy <tag>` (e.g. `1.0.0-2026.11.22`) runs the checks (git, image labels),
these commands and the verification (health, row counts, public endpoints).

## Reverse proxy

Point the public address (e.g. `https://example.org/campus/`) to
`$FC_PORT` and set `X-Forwarded-Proto: https`, so that the session cookie is
`Secure`. The site works whether or not the proxy strips the prefix.

## Logins and passwords

Edit the local `data/campus.env` and write it into the volume as in the first
start, then restart the container. At start the server creates new people,
updates roles and applies changed passwords; sessions of a person whose
password changed are ended. `/fc-deploy` compares checksums of the local and
the server's file (never the content) and offers to apply them.

## Backup

```bash
sudo docker run --rm -v $FC_VOLUME:/data -v "$PWD:/backup" --user root --entrypoint sh $FC_IMAGE \
  -c 'python3 -c "import sqlite3; sqlite3.connect(\"/data/campus.sqlite\").backup(sqlite3.connect(\"/backup/campus-$(date +%F).sqlite\"))"'
```

Back up `campus.env` separately if needed.

## Moving to a new volume

A volume cannot be renamed. Set `FC_MIGRATE_FROM_VOLUME` and
`FC_MIGRATE_FROM_CONTAINER` in `deploy.env`; `/fc-deploy` then stops the old
container, copies the old volume (mounted read-only) into `FC_VOLUME`,
compares checksums, starts the new container and keeps the old volume as a
backup. Remove the two lines afterwards.

## Releases

my-family has no version of its own (ADR-0018). A tile that was improved gets
`updated` and a short `note` in `tiles.json` (new tiles have their `date`) –
that is what learners see in "What's new?". Then:

```bash
tools/campus-build.sh                 # build and checks
# only if my-family/ is its own git repository:
git -C my-family add -A && git -C my-family commit -m "New tiles: …" && git -C my-family push
tools/campus-image.sh                 # → $FC_IMAGE:<version>-<date> and :latest
docker push $FC_IMAGE:<version>-<date> && docker push $FC_IMAGE:latest
```

After an update of Family Campus (`git pull`) set `FC_APP_VERSION` in
`deploy.env` to its new `VERSION`; its notes for learners come with it.

## Releasing Family Campus

Family Campus has the only version: `VERSION`, `CHANGELOG.md` (for
developers) and `release-notes.json` (for learners, at least `en` and `de`).
Before a release run
`tools/publish_check.sh --deny <file>`: it checks every file that would be
committed against a list of private words kept **outside** the repository
(names, domains, servers of your family), looks for secrets and databases,
checks LICENSE, README, changelog and release notes, builds the example
family, runs the i18n check and the self test. Then tag `v<version>`. Each
my-family moves to the new version by changing `FC_APP_VERSION`.

## Checks

- `GET /healthz` → `ok`
- `docker logs $FC_CONTAINER` → `Family Campus <version> on :8080`,
  `user created: …`, `password changed: …`
