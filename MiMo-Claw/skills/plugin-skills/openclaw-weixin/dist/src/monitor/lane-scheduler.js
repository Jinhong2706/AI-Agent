export function createLaneScheduler() {
    /**
     * laneKey -> tail promise of the lane's in-flight chain. The chain is built
     * with internal `try/catch` so failures of earlier tasks do not poison later
     * tasks on the same lane. Entries are pruned when the lane goes idle.
     */
    const lanes = new Map();
    function enqueue(key, task) {
        const previousTail = lanes.get(key) ?? Promise.resolve();
        let resolveResult;
        let rejectResult;
        const result = new Promise((resolve, reject) => {
            resolveResult = resolve;
            rejectResult = reject;
        });
        const nextTail = previousTail.then(async () => {
            try {
                const value = await task();
                resolveResult(value);
            }
            catch (err) {
                rejectResult(err);
            }
        });
        lanes.set(key, nextTail);
        void nextTail.finally(() => {
            // Only prune if no one queued behind us in the meantime; otherwise the
            // newer enqueue() owns the slot.
            if (lanes.get(key) === nextTail) {
                lanes.delete(key);
            }
        });
        return result;
    }
    function size() {
        return lanes.size;
    }
    async function drain() {
        while (lanes.size > 0) {
            const tails = [...lanes.values()];
            await Promise.allSettled(tails);
        }
    }
    return { enqueue, size, drain };
}
//# sourceMappingURL=lane-scheduler.js.map