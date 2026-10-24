# Method references and dependencies

Photo Finish's workflow and controller code are distributed under the repository MIT license. The public package contains no copied upstream engine, model weights, third-party photographs or fonts.

The following projects informed independently written photographic methods; attribution is retained and their code is not bundled or relicensed here:

| Project | Method considered | Source |
|---|---|---|
| f1shh/my-skills | Style briefs, light/color relationships and review of rendered results | https://github.com/f1shh/my-skills/tree/main/photo-xmp-editing |
| Automaat/lightroom-mcp | Capability discovery and separation of technical and creative RAW duties | https://github.com/Automaat/lightroom-mcp |
| OpenCLIP | Considered as a semantic-retrieval alternative; not installed or executed by this skill | https://github.com/mlfoundations/open_clip |

The detailed [method adaptation record](references/professional-development.md) preserves source file references. No upstream execution behavior or license obligation is assumed simply from a method citation.

The independently written [tone/color foundations](references/tone-color-foundations.md) distinguish a paraphrased, approximately 75-second still-life tutorial from Adobe's official tone, color and masking documentation and this skill's own application reasoning. The tutorial's author, title and public URL were not supplied; no creator is invented. No tutorial media, screenshots or full transcript are bundled. The source links support tool mechanisms, not universal aesthetic claims or measured photo-quality gains.

Pillow is the core separately installed Python dependency. NumPy and SciPy are optional numerical-analysis dependencies. Each retains its own license; none is vendored into the skill archive. Lightroom, other editors, image providers and host agents are external services governed by their own terms. The MIT license does not license user photographs, image-service outputs or third-party trademarks.
