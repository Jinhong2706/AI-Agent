import * as _$openclaw_plugin_sdk_channel_entry_contract0 from "openclaw/plugin-sdk/channel-entry-contract";
import * as _$openclaw_plugin_sdk0 from "openclaw/plugin-sdk";

//#region entry-bundled.d.ts
/**
 * Bundled entry for openclaw-fork compatibility.
 *
 * Standard openclaw loads the plugin via `index.ts` (export default register).
 * openclaw-fork expects `defineBundledChannelEntry` format.
 *
 * Usage in package.json exports:
 *   "./bundled" → this file
 */
declare const _default: _$openclaw_plugin_sdk_channel_entry_contract0.BundledChannelEntryContract<_$openclaw_plugin_sdk0.ChannelPlugin>;
//#endregion
export { _default as default };