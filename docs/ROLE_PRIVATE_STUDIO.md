# Role Private Studio

`Role Private Studio` is the canonical SA-NOM surface for defining organization-specific AI hats from normal working material such as job descriptions, operating briefs, and role outlines.

It should be read as the current product name for the capability that lets teams shape real governed AI roles without writing PTAG directly.

## What It Does

With `Role Private Studio`, an organization can:

- upload or paste a normal JD-style document
- start from a starter JD, starter role outline, or starter hat prepared by SA-NOM
- adapt the role to fit local reporting lines, authority boundaries, and escalation rules
- let SA-NOM transform that material into PTAG-backed governed role packs behind the scenes
- move the resulting role through review, publication, and trusted runtime readiness

The point is not to expose governance language to every operator.
The point is to let organizations describe real work in normal documents while SA-NOM converts that work into governed runtime structure.

## What The User Sees

The user-facing input should look like a normal role or operating document:

- role or hat name
- purpose
- reporting line
- allowed actions
- human-required actions
- forbidden actions
- escalation or exception posture

Behind the scenes, SA-NOM turns that into structured governed material that can be reviewed, published, and used by the runtime.

## What Kind Of Hats It Supports

The platform is not limited to standard titles.
Organizations can define governed hats such as:

- `Factory Recovery Coordinator`
- `Customer Claim War Room Lead`
- `Launch Freeze Exception Coordinator`
- `Group Procurement Policy Escalation Lead`
- `Bank Regulator Liaison Lead`

These may be permanent roles, temporary hats, cross-functional seats, or narrow escalation responsibilities.

## Core Capability, Not A Paid Unlock

`Role Private Studio` is part of the core SA-NOM platform story.

Commercial work should focus on:

- organization-specific tailoring
- workshops and rollout support
- starter-library preparation
- industry-specific governance design
- publication and operating-model enablement

The ability to create organization-defined governed hats should remain part of the platform baseline.

## Relationship To Historical Naming

Earlier repository notes used the terms `Private Rule Studio` and `Private Rule Position`.

Those terms should now be read as older concept language.
The current canonical product name is `Role Private Studio`.

See [PRIVATE_RULE_POSITION.md](PRIVATE_RULE_POSITION.md) if you need the historical note for older references or release history.

## Example Artifact

See [../examples/role_private_studio.example.json](../examples/role_private_studio.example.json) for the current public-safe example input shape.
