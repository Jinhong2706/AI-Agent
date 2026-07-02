import { z as z$1 } from "zod";
import { ChannelPlugin, OpenClawPluginApi, PluginRuntime } from "openclaw/plugin-sdk";

//#region src/config/schema.d.ts
declare const DingtalkConfigSchema: z$1.ZodObject<{
  dmPolicy: z$1.ZodDefault<z$1.ZodOptional<z$1.ZodEnum<{
    open: "open";
    pairing: "pairing";
    allowlist: "allowlist";
  }>>>;
  groupPolicy: z$1.ZodDefault<z$1.ZodOptional<z$1.ZodEnum<{
    open: "open";
    allowlist: "allowlist";
    disabled: "disabled";
  }>>>;
  requireMention: z$1.ZodDefault<z$1.ZodOptional<z$1.ZodBoolean>>;
  separateSessionByConversation: z$1.ZodDefault<z$1.ZodOptional<z$1.ZodBoolean>>;
  sharedMemoryAcrossConversations: z$1.ZodDefault<z$1.ZodOptional<z$1.ZodBoolean>>;
  groupSessionScope: z$1.ZodDefault<z$1.ZodOptional<z$1.ZodOptional<z$1.ZodEnum<{
    group: "group";
    group_sender: "group_sender";
  }>>>>;
  accounts: z$1.ZodOptional<z$1.ZodRecord<z$1.ZodString, z$1.ZodOptional<z$1.ZodObject<{
    dmPolicy: z$1.ZodOptional<z$1.ZodEnum<{
      open: "open";
      pairing: "pairing";
      allowlist: "allowlist";
    }>>;
    allowFrom: z$1.ZodOptional<z$1.ZodArray<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>>;
    groupPolicy: z$1.ZodOptional<z$1.ZodEnum<{
      open: "open";
      allowlist: "allowlist";
      disabled: "disabled";
    }>>;
    groupAllowFrom: z$1.ZodOptional<z$1.ZodArray<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>>;
    requireMention: z$1.ZodOptional<z$1.ZodBoolean>;
    groups: z$1.ZodOptional<z$1.ZodRecord<z$1.ZodString, z$1.ZodOptional<z$1.ZodObject<{
      requireMention: z$1.ZodOptional<z$1.ZodBoolean>;
      tools: z$1.ZodOptional<z$1.ZodObject<{
        allow: z$1.ZodOptional<z$1.ZodArray<z$1.ZodString>>;
        deny: z$1.ZodOptional<z$1.ZodArray<z$1.ZodString>>;
      }, z$1.core.$strict>>;
      enabled: z$1.ZodOptional<z$1.ZodBoolean>;
      allowFrom: z$1.ZodOptional<z$1.ZodArray<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>>;
      systemPrompt: z$1.ZodOptional<z$1.ZodString>;
      groupSessionScope: z$1.ZodOptional<z$1.ZodEnum<{
        group: "group";
        group_sender: "group_sender";
      }>>;
    }, z$1.core.$strict>>>>;
    historyLimit: z$1.ZodOptional<z$1.ZodNumber>;
    textChunkLimit: z$1.ZodOptional<z$1.ZodNumber>;
    mediaMaxMb: z$1.ZodOptional<z$1.ZodNumber>;
    tools: z$1.ZodOptional<z$1.ZodObject<{
      docs: z$1.ZodOptional<z$1.ZodBoolean>;
      media: z$1.ZodOptional<z$1.ZodBoolean>;
    }, z$1.core.$strict>>;
    typingIndicator: z$1.ZodOptional<z$1.ZodBoolean>;
    resolveSenderNames: z$1.ZodOptional<z$1.ZodBoolean>;
    separateSessionByConversation: z$1.ZodOptional<z$1.ZodBoolean>;
    sharedMemoryAcrossConversations: z$1.ZodOptional<z$1.ZodBoolean>;
    groupSessionScope: z$1.ZodOptional<z$1.ZodEnum<{
      group: "group";
      group_sender: "group_sender";
    }>>;
    asyncMode: z$1.ZodOptional<z$1.ZodBoolean>;
    ackText: z$1.ZodOptional<z$1.ZodString>;
    endpoint: z$1.ZodOptional<z$1.ZodString>;
    debug: z$1.ZodOptional<z$1.ZodBoolean>;
    enableMediaUpload: z$1.ZodOptional<z$1.ZodBoolean>;
    systemPrompt: z$1.ZodOptional<z$1.ZodString>;
    groupReplyMode: z$1.ZodOptional<z$1.ZodEnum<{
      aicard: "aicard";
      text: "text";
      markdown: "markdown";
    }>>;
    enabled: z$1.ZodOptional<z$1.ZodBoolean>;
    name: z$1.ZodOptional<z$1.ZodString>;
    clientId: z$1.ZodOptional<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>;
    clientSecret: z$1.ZodOptional<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodObject<{
      source: z$1.ZodEnum<{
        file: "file";
        env: "env";
        exec: "exec";
      }>;
      provider: z$1.ZodString;
      id: z$1.ZodString;
    }, z$1.core.$strip>]>>;
    chatbotUserId: z$1.ZodOptional<z$1.ZodString>;
    chatbotCorpId: z$1.ZodOptional<z$1.ZodString>;
  }, z$1.core.$strict>>>>;
  allowFrom: z$1.ZodOptional<z$1.ZodArray<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>>;
  groupAllowFrom: z$1.ZodOptional<z$1.ZodArray<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>>;
  groups: z$1.ZodOptional<z$1.ZodRecord<z$1.ZodString, z$1.ZodOptional<z$1.ZodObject<{
    requireMention: z$1.ZodOptional<z$1.ZodBoolean>;
    tools: z$1.ZodOptional<z$1.ZodObject<{
      allow: z$1.ZodOptional<z$1.ZodArray<z$1.ZodString>>;
      deny: z$1.ZodOptional<z$1.ZodArray<z$1.ZodString>>;
    }, z$1.core.$strict>>;
    enabled: z$1.ZodOptional<z$1.ZodBoolean>;
    allowFrom: z$1.ZodOptional<z$1.ZodArray<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>>;
    systemPrompt: z$1.ZodOptional<z$1.ZodString>;
    groupSessionScope: z$1.ZodOptional<z$1.ZodEnum<{
      group: "group";
      group_sender: "group_sender";
    }>>;
  }, z$1.core.$strict>>>>;
  historyLimit: z$1.ZodOptional<z$1.ZodNumber>;
  textChunkLimit: z$1.ZodOptional<z$1.ZodNumber>;
  mediaMaxMb: z$1.ZodOptional<z$1.ZodNumber>;
  tools: z$1.ZodOptional<z$1.ZodObject<{
    docs: z$1.ZodOptional<z$1.ZodBoolean>;
    media: z$1.ZodOptional<z$1.ZodBoolean>;
  }, z$1.core.$strict>>;
  typingIndicator: z$1.ZodOptional<z$1.ZodBoolean>;
  resolveSenderNames: z$1.ZodOptional<z$1.ZodBoolean>;
  asyncMode: z$1.ZodOptional<z$1.ZodBoolean>;
  ackText: z$1.ZodOptional<z$1.ZodString>;
  endpoint: z$1.ZodOptional<z$1.ZodString>;
  debug: z$1.ZodOptional<z$1.ZodBoolean>;
  enableMediaUpload: z$1.ZodOptional<z$1.ZodBoolean>;
  systemPrompt: z$1.ZodOptional<z$1.ZodString>;
  groupReplyMode: z$1.ZodOptional<z$1.ZodEnum<{
    aicard: "aicard";
    text: "text";
    markdown: "markdown";
  }>>;
  enabled: z$1.ZodOptional<z$1.ZodBoolean>;
  defaultAccount: z$1.ZodOptional<z$1.ZodString>;
  clientId: z$1.ZodOptional<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodNumber]>>;
  clientSecret: z$1.ZodOptional<z$1.ZodUnion<readonly [z$1.ZodString, z$1.ZodObject<{
    source: z$1.ZodEnum<{
      file: "file";
      env: "env";
      exec: "exec";
    }>;
    provider: z$1.ZodString;
    id: z$1.ZodString;
  }, z$1.core.$strip>]>>;
}, z$1.core.$strict>;
//#endregion
//#region src/types/index.d.ts
type DingtalkConfig = z$1.infer<typeof DingtalkConfigSchema>;
type DingtalkDefaultAccountSelectionSource = "explicit-default" | "mapped-default" | "fallback";
type DingtalkAccountSelectionSource = "explicit" | DingtalkDefaultAccountSelectionSource;
type ResolvedDingtalkAccount = {
  accountId: string;
  selectionSource: DingtalkAccountSelectionSource;
  enabled: boolean;
  configured: boolean;
  name?: string;
  clientId?: string;
  clientSecret?: string; /** Merged config (top-level defaults + account-specific overrides) */
  config: DingtalkConfig;
};
//#endregion
//#region src/channel.d.ts
declare const dingtalkPlugin: ChannelPlugin<ResolvedDingtalkAccount>;
/**
 * Synchronously initializes `dingtalkPlugin.configSchema` using `createRequire`.
 *
 * Static `import ... from "openclaw/plugin-sdk/core"` causes
 * "Cannot find package 'openclaw'" when the plugin is installed to
 * `~/.openclaw/extensions/` (Issue #527) because the ESM loader resolves
 * bare specifiers at parse time before the gateway's jiti alias map is active.
 *
 * By deferring the resolve to `register()` time and using `createRequire`
 * (which searches the gateway's own `node_modules`), we avoid the crash
 * while keeping the call synchronous as required by the plugin API.
 */
declare function initDingtalkPluginConfigSchema(): void;
//#endregion
//#region src/runtime.d.ts
declare const setDingtalkRuntime: (next: PluginRuntime) => void, getDingtalkRuntime: () => PluginRuntime;
//#endregion
//#region src/gateway-methods.d.ts
/**
 * 注册所有 Gateway Methods
 */
declare function registerGatewayMethods(api: OpenClawPluginApi): void;
//#endregion
//#region index.d.ts
declare function register(api: OpenClawPluginApi): void;
//#endregion
export { register as default, dingtalkPlugin, initDingtalkPluginConfigSchema, registerGatewayMethods, setDingtalkRuntime };