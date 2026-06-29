## Description: <br>
Searches MuseScore sheet music, reads score metadata, and helps resolve download or PDF outputs through a configured musescore-mcp server and fetchproxy browser session. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[chrischall](https://clawhub.ai/user/chrischall) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and external users use this skill to help an agent search MuseScore, inspect score metadata, and prepare download or PDF workflows through a separately installed MCP server and browser bridge. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: MuseScore requests are routed through a signed-in browser tab and depend on external MCP and fetchproxy components that are not included in the submitted artifact. <br>
Mitigation: Review the external components before installation, keep authentication in the browser session, and use the skill only in environments where that routing model is acceptable. <br>


## Reference(s): <br>
- [ClawHub release page](https://clawhub.ai/chrischall/musescore-mcp) <br>
- [musescore-mcp project referenced by the skill documentation](https://github.com/chrischall/musescore-mcp) <br>
- [fetchproxy browser extension referenced by the skill documentation](https://github.com/chrischall/fetchproxy) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, configuration, shell commands, guidance] <br>
**Output Format:** [Markdown with configuration snippets and MCP tool guidance] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May return MuseScore metadata, download links, health-check results, or local PDF workflow guidance depending on the configured MCP tools.] <br>

## Skill Version(s): <br>
0.12.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
