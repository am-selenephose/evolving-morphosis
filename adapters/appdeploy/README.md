# AppDeploy adapter

Tracked source overlay for the public Morphosis AppDeploy deployment.

- App id: `evolving-morphosis-t84odc`
- Captured deployed source version: `1789898522623` (v17)
- Canonical decision authority: `src/morphosis/os/`
- Canonical shared UI: `site/index.html`, `site/app.js`, `site/styles.css`, `site/visuals.js`
- Adapter-specific projection client: `data.js`
- Adapter-specific persistence/API/realtime: `backend/`
- Platform QA contract: `tests/tests.json`

The four shared UI files above were verified byte-for-byte equal to the deployed v17 source before this overlay was captured. `data.js` intentionally differs because AppDeploy uses `@appdeploy/client`; the canonical repository client remains platform-independent.

This adapter must not be treated as an independent Morphosis authority. It may persist and present deterministic proof fixtures, but it must not claim external model execution, production AgentCore traffic, or permission to merge source changes automatically.

Unused AppDeploy template scaffold files under `src/` are deliberately not vendored here because the deployed root `index.html` loads `app.js` directly.
