/**
 * Model selection buttons for Weixin.
 *
 * Reuses the same mdl_* callback_data format as Telegram so that core
 * helpers (buildModelsProviderData, formatModelsAvailableHeader) can be
 * shared directly.
 *
 * Callback data patterns:
 * - mdl_prov              - show providers list
 * - mdl_list_{prov}_{pg}  - show models for provider (page N, 1-indexed)
 * - mdl_sel_{provider/id} - select model
 * - mdl_back              - back to providers list
 */
const MODELS_PAGE_SIZE = 8;
// ---------------------------------------------------------------------------
// Callback data parsing
// ---------------------------------------------------------------------------
export function parseModelCallbackData(data) {
    const trimmed = data.trim();
    if (!trimmed.startsWith("mdl_"))
        return null;
    if (trimmed === "mdl_prov" || trimmed === "mdl_back") {
        return { type: trimmed === "mdl_prov" ? "providers" : "back" };
    }
    const listMatch = trimmed.match(/^mdl_list_([a-z0-9_-]+)_(\d+)$/i);
    if (listMatch) {
        const [, provider, pageStr] = listMatch;
        const page = Number.parseInt(pageStr ?? "1", 10);
        if (provider && Number.isFinite(page) && page >= 1) {
            return { type: "list", provider, page };
        }
    }
    const selMatch = trimmed.match(/^mdl_sel_(.+)$/);
    if (selMatch) {
        const modelRef = selMatch[1];
        if (modelRef) {
            const slashIndex = modelRef.indexOf("/");
            if (slashIndex > 0 && slashIndex < modelRef.length - 1) {
                return {
                    type: "select",
                    provider: modelRef.slice(0, slashIndex),
                    model: modelRef.slice(slashIndex + 1),
                };
            }
            return { type: "select", model: modelRef };
        }
    }
    return null;
}
// ---------------------------------------------------------------------------
// Keyboard builders
// ---------------------------------------------------------------------------
export function buildProviderKeyboard(providers) {
    if (providers.length === 0)
        return [];
    const rows = [];
    let currentRow = [];
    for (const provider of providers) {
        currentRow.push({
            text: `${provider.id} (${provider.count})`,
            callback_data: `mdl_list_${provider.id}_1`,
        });
        if (currentRow.length === 2) {
            rows.push(currentRow);
            currentRow = [];
        }
    }
    if (currentRow.length > 0)
        rows.push(currentRow);
    return rows;
}
function truncateModelId(modelId, maxLen) {
    if (modelId.length <= maxLen)
        return modelId;
    return `…${modelId.slice(-(maxLen - 1))}`;
}
export function buildModelsKeyboard(params) {
    const { provider, models, currentModel, currentPage, totalPages, modelNames } = params;
    const pageSize = params.pageSize ?? MODELS_PAGE_SIZE;
    if (models.length === 0) {
        return [[{ text: "<< Back", callback_data: "mdl_back" }]];
    }
    const rows = [];
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, models.length);
    const pageModels = models.slice(startIndex, endIndex);
    for (const model of pageModels) {
        const callbackData = `mdl_sel_${provider}/${model}`;
        const isCurrentModel = currentModel
            ? currentModel.includes("/")
                ? currentModel === `${provider}/${model}`
                : currentModel === model
            : false;
        const displayLabel = modelNames?.get(`${provider}/${model}`) ?? model;
        const displayText = truncateModelId(displayLabel, 38);
        const text = isCurrentModel ? `${displayText} ✓` : displayText;
        rows.push([{ text, callback_data: callbackData }]);
    }
    if (totalPages > 1) {
        const paginationRow = [];
        if (currentPage > 1) {
            paginationRow.push({
                text: "◀ Prev",
                callback_data: `mdl_list_${provider}_${currentPage - 1}`,
            });
        }
        paginationRow.push({
            text: `${currentPage}/${totalPages}`,
            callback_data: `mdl_list_${provider}_${currentPage}`,
        });
        if (currentPage < totalPages) {
            paginationRow.push({
                text: "Next ▶",
                callback_data: `mdl_list_${provider}_${currentPage + 1}`,
            });
        }
        rows.push(paginationRow);
    }
    rows.push([{ text: "<< Back", callback_data: "mdl_back" }]);
    return rows;
}
export function buildBrowseProvidersButton() {
    return [[{ text: "Browse providers", callback_data: "mdl_prov" }]];
}
export function getModelsPageSize() {
    return MODELS_PAGE_SIZE;
}
export function calculateTotalPages(totalModels, pageSize) {
    const size = pageSize ?? MODELS_PAGE_SIZE;
    return size > 0 ? Math.ceil(totalModels / size) : 1;
}
// ---------------------------------------------------------------------------
// channelData builders (used by plugin.commands adapter)
// ---------------------------------------------------------------------------
export function buildWeixinModelsProviderChannelData(params) {
    if (params.providers.length === 0)
        return null;
    return { "openclaw-weixin": { buttons: buildProviderKeyboard(params.providers) } };
}
export function buildWeixinModelsListChannelData(params) {
    return { "openclaw-weixin": { buttons: buildModelsKeyboard(params) } };
}
export function buildWeixinModelBrowseChannelData() {
    return { "openclaw-weixin": { buttons: buildBrowseProvidersButton() } };
}
export function buildWeixinCommandsListChannelData(params) {
    if (params.totalPages <= 1)
        return null;
    const buttons = [];
    const suffix = params.agentId ? `:${params.agentId}` : "";
    if (params.currentPage > 1) {
        buttons.push({
            text: "◀ Prev",
            callback_data: `commands_page_${params.currentPage - 1}${suffix}`,
        });
    }
    buttons.push({
        text: `${params.currentPage}/${params.totalPages}`,
        callback_data: `commands_page_noop${suffix}`,
    });
    if (params.currentPage < params.totalPages) {
        buttons.push({
            text: "Next ▶",
            callback_data: `commands_page_${params.currentPage + 1}${suffix}`,
        });
    }
    return { "openclaw-weixin": { buttons: [buttons] } };
}
// ---------------------------------------------------------------------------
// Model selection resolution (when provider is ambiguous)
// ---------------------------------------------------------------------------
export function resolveModelSelection(params) {
    if (params.callback.provider) {
        return { kind: "resolved", provider: params.callback.provider, model: params.callback.model };
    }
    const matchingProviders = params.providers.filter((id) => params.byProvider.get(id)?.has(params.callback.model));
    if (matchingProviders.length === 1) {
        return { kind: "resolved", provider: matchingProviders[0], model: params.callback.model };
    }
    return { kind: "ambiguous", model: params.callback.model, matchingProviders };
}
//# sourceMappingURL=model-buttons.js.map