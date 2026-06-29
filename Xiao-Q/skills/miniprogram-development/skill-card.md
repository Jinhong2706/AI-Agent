## Description: <br>
Assists developers with building, debugging, previewing, publishing, and optimizing WeChat Mini Program projects, including applicable CloudBase workflows. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[binggg](https://clawhub.ai/user/binggg) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and engineers use this skill to create, modify, debug, preview, test, deploy, and optimize WeChat Mini Program projects. It also guides CloudBase integration when the project explicitly uses wx.cloud or Tencent CloudBase. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Preview, upload, publish, or CloudBase MCP actions can target the wrong WeChat Mini Program or CloudBase environment. <br>
Mitigation: Confirm the project, AppID, CloudBase environment, and account before allowing the agent to preview, upload, publish, or configure CloudBase tooling. <br>
Risk: CloudBase workflows may involve OAuth tokens or sensitive credentials. <br>
Mitigation: Use interactive authentication where available, avoid hard-coding secrets, and grant only the CloudBase permissions needed for the task. <br>
Risk: Generated mini program code can fail in WeChat Developer Tools or on real devices when platform constraints are overlooked. <br>
Mitigation: Validate project configuration and test in WeChat Developer Tools or on a real device, especially after changes involving assets, tab bars, CloudBase initialization, or modern JavaScript syntax. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/binggg/miniprogram-development) <br>
- [CloudBase Mini Program Integration](references/cloudbase-integration.md) <br>
- [Common Pitfalls in WeChat Mini Program Development](references/pitfalls.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Code, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Markdown with inline code blocks and structured implementation guidance] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include project file changes, configuration snippets, preview or upload commands, and CloudBase workflow guidance when requested.] <br>

## Skill Version(s): <br>
1.28.0 (source: server release metadata; artifact frontmatter reports 2.21.1) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
