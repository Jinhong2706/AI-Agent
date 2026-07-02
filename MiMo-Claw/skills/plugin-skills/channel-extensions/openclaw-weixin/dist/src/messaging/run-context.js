import { AsyncLocalStorage } from "node:async_hooks";
const turnContextStorage = new AsyncLocalStorage();
export function withWeixinTurnContext(ctx, run) {
    return turnContextStorage.run(ctx, run);
}
export function getCurrentWeixinTurnContext() {
    return turnContextStorage.getStore();
}
//# sourceMappingURL=run-context.js.map