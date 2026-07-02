/**
 * Handle mdl_* button callbacks for /model interactive flow.
 *
 * When a user taps a model-selection button, the BUTTON_CALLBACK arrives
 * as an inbound message with call_back_data = "mdl_...".  We intercept
 * it here, build the next response (provider list / model list / confirmation),
 * and send a NEW message (no editing).
 */
import { buildModelsProviderData, formatModelsAvailableHeader } from "openclaw/plugin-sdk/models-provider-runtime";
import { resolveAgentDir, resolveDefaultModelForAgent } from "openclaw/plugin-sdk/agent-runtime";
import { applyModelOverrideToSessionEntry, updateSessionStore, resolveStorePath, } from "openclaw/plugin-sdk/config-runtime";
import { logger } from "../util/logger.js";
import { sendMessageWeixin } from "./send.js";
import { getContextToken } from "./inbound.js";
import { parseModelCallbackData, buildProviderKeyboard, buildModelsKeyboard, calculateTotalPages, getModelsPageSize, resolveModelSelection, } from "./model-buttons.js";
/**
 * Try to handle an inbound message as a model callback.
 * Returns true if the callback was handled, false otherwise.
 */
export async function handleModelCallback(callbackData, deps) {
    const parsed = parseModelCallbackData(callbackData);
    if (!parsed)
        return false;
    const contextToken = getContextToken(deps.accountId, deps.to);
    const sendOpts = { baseUrl: deps.baseUrl, token: deps.token, contextToken };
    const modelData = await buildModelsProviderData(deps.cfg, deps.agentId);
    const { byProvider, providers } = modelData;
    const sendWithButtons = async (text, buttons) => {
        await sendMessageWeixin({
            to: deps.to,
            text,
            opts: sendOpts,
            buttons: buttons.length > 0 ? buttons : undefined,
        });
    };
    if (parsed.type === "providers" || parsed.type === "back") {
        if (providers.length === 0) {
            await sendWithButtons("No providers available.", []);
            return true;
        }
        const providerInfos = providers.map((p) => ({
            id: p,
            count: byProvider.get(p)?.size ?? 0,
        }));
        await sendWithButtons("Select a provider:", buildProviderKeyboard(providerInfos));
        return true;
    }
    if (parsed.type === "list") {
        const { provider, page } = parsed;
        const modelSet = byProvider.get(provider);
        if (!modelSet || modelSet.size === 0) {
            const providerInfos = providers.map((p) => ({
                id: p,
                count: byProvider.get(p)?.size ?? 0,
            }));
            await sendWithButtons(`Unknown provider: ${provider}\n\nSelect a provider:`, buildProviderKeyboard(providerInfos));
            return true;
        }
        const models = [...modelSet].toSorted();
        const pageSize = getModelsPageSize();
        const totalPages = calculateTotalPages(models.length, pageSize);
        const safePage = Math.max(1, Math.min(page, totalPages));
        const currentModel = undefined; // TODO: resolve from session if needed
        const buttons = buildModelsKeyboard({
            provider,
            models,
            currentModel,
            currentPage: safePage,
            totalPages,
            pageSize,
            modelNames: modelData.modelNames,
        });
        const text = formatModelsAvailableHeader({
            provider,
            total: models.length,
            cfg: deps.cfg,
            agentDir: deps.agentId ? resolveAgentDir(deps.cfg, deps.agentId) : undefined,
        });
        await sendWithButtons(text, buttons);
        return true;
    }
    if (parsed.type === "select") {
        const selection = resolveModelSelection({
            callback: parsed,
            providers,
            byProvider,
        });
        if (selection.kind !== "resolved") {
            const providerInfos = providers.map((p) => ({
                id: p,
                count: byProvider.get(p)?.size ?? 0,
            }));
            await sendWithButtons(`Could not resolve model "${selection.model}".\n\nSelect a provider:`, buildProviderKeyboard(providerInfos));
            return true;
        }
        const modelSet = byProvider.get(selection.provider);
        if (!modelSet?.has(selection.model)) {
            await sendWithButtons(`❌ Model "${selection.provider}/${selection.model}" is not allowed.`, []);
            return true;
        }
        try {
            const storePath = resolveStorePath(deps.cfg.session?.store, { agentId: deps.agentId }) ?? "";
            const resolvedDefault = resolveDefaultModelForAgent({ cfg: deps.cfg, agentId: deps.agentId });
            const isDefaultSelection = selection.provider === resolvedDefault.provider &&
                selection.model === resolvedDefault.model;
            await updateSessionStore(storePath, (store) => {
                if (!deps.sessionKey)
                    return;
                const entry = store[deps.sessionKey] ?? {};
                store[deps.sessionKey] = entry;
                applyModelOverrideToSessionEntry({
                    entry,
                    selection: {
                        provider: selection.provider,
                        model: selection.model,
                        isDefault: isDefaultSelection,
                    },
                });
            });
            const actionText = isDefaultSelection
                ? "reset to default"
                : `changed to ${selection.provider}/${selection.model}`;
            await sendWithButtons(`✅ Model ${actionText}\n\nThis model will be used for your next message.`, []);
        }
        catch (err) {
            logger.error(`handleModelCallback: failed to set model: ${String(err)}`);
            await sendWithButtons(`❌ Failed to set model: ${String(err)}`, []);
        }
        return true;
    }
    return false;
}
//# sourceMappingURL=model-callback-handler.js.map