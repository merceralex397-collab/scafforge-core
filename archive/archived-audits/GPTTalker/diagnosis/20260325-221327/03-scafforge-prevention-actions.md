# Report 3: Scafforge Prevention Actions

These actions describe package-side changes that prevent the same failures from reappearing in future generated repos.

- Reject unsupported stage probing and explicit workflow bypass attempts in both generated tools and prompt hardening.

- Make `ticket_reverify` the legal trust-restoration path for closed done tickets instead of binding it to the normal closed-ticket lease rules.

- Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure.

- Teach audit and repair to treat pending backlog process verification as a first-class verification state so repaired repos are not declared clean while historical done tickets remain untrusted.

