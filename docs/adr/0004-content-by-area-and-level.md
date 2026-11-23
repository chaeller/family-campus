# ADR-0004: Content belongs to areas and levels, not to people

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

The same family has children at school, young people in an apprenticeship
and adults in further education. Content made for one person should serve
the next one who reaches the same stage, and level names repeat between
trainings ("1st year").

## Decision

- Content is organised as **category → area → level**: categories (school,
  vocational training, studies, further education, general knowledge) hold
  areas (e.g. one school system, one profession), areas hold ordered levels
  or none. Ids are English; names are given per locale.
- Every tile has an `area` and, if the area has levels, a `level`. Every
  person has a current area and level.
- A selected person sees their area up to their level; an area marked
  `levelOnly` starts on exactly the person's level. Areas marked `forAll`
  (general knowledge) are for everybody and have their own entry in the
  filter.
- Only exams and focus lists are bound to people.

## Consequences

+ Tiles are reusable across people and years.
+ Shortened or extended trainings are mapped through the person's level.
− my-family has to describe its areas and levels before adding tiles.

## Alternatives considered

- **Tiles per person:** content would be duplicated and lost when a person moves on.
- **Free tags:** no order of levels, no "up to my level".
