# Package Publishing and Installation

`@scafforge/core` is configured for public npm publication.

## Package state

- `package.json` no longer marks the package as `private`
- `publishConfig.access` is set to `public` for the scoped package publish path
- repository, homepage, bugs, keywords, and packaged file metadata are declared
- runtime requirements remain:
  - Node.js 20+
  - Python 3.10+

## Install a published release

After a version has been published to npm:

```bash
npm install --global @scafforge/core
scafforge --help
```

If you prefer one-off execution after publication:

```bash
npx @scafforge/core --help
```

## Use a local checkout before release

Until a registry version is actually published, or when validating unreleased changes from a checkout:

```bash
npm install --global .
scafforge --help
```

Or invoke the bin wrapper directly:

```bash
node ./bin/scafforge.mjs --help
```

## Publish from this repository

From the repository root:

```bash
npm publish
```

`publishConfig.access` already declares the public access level, so no extra access flag is required for the normal release path.
