## Description: <br>
Use this skill when a SaaS founder, indie hacker, or product builder wants to turn product updates, user pain points, technical lessons, launches, or founder observations into high-signal posts for X, Reddit, LinkedIn, or Xiaohongshu, including HTML/CSS-rendered covers and data cards for image-first platforms. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[archlab-space](https://clawhub.ai/user/archlab-space) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External SaaS founders, indie hackers, and product builders use this skill to turn concrete product updates, user pain points, technical lessons, usage data, launches, or feedback requests into platform-fit social posts. It supports X, Reddit, LinkedIn, and Xiaohongshu, with optional guidance for text- and data-driven image cards. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Generated social posts can contain misleading marketing claims if the founder's raw material is vague, incomplete, or unverified. <br>
Mitigation: Require concrete source material, avoid inventing metrics, quotes, testimonials, or features, and review each draft before publishing. <br>
Risk: Platform promotion rules vary, especially for Reddit communities and Xiaohongshu notes. <br>
Mitigation: Check the current platform or community rules before posting, keep promotion soft where required, and disclose founder affiliation when relevant. <br>
Risk: The optional image renderer runs a local headless browser on HTML input. <br>
Mitigation: Render only HTML created by the user or agent, avoid untrusted external assets, and do not place secrets in templates or output paths. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/archlab-space/saas-founder-content-writer) <br>
- [Issue and contribution link](https://github.com/archlab-space/open-skill-hub/issues) <br>
- [Render Image Setup](render-image-setup.md) <br>
- [Xiaohongshu Cover Template](assets/xiaohongshu-cover.html) <br>
- [Data Card Template](assets/data-card.html) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, guidance] <br>
**Output Format:** [Markdown draft blocks with angle, platform, post text, image recommendation or image brief, rationale, and self-review; may include HTML/CSS snippets and render commands for image cards.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires founder-provided product context and raw material before drafting; Xiaohongshu outputs include a required cover recommendation.] <br>

## Skill Version(s): <br>
0.7.0 (source: server release evidence and CHANGELOG, released 2026-06-05) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
