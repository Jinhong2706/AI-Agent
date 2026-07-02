import crypto from "node:crypto";
import { initStream, syncStream } from "../api/api.js";
import { AbortType } from "../api/types.js";
import { getOrCreateDeviceId } from "../auth/accounts.js";
import { logger } from "../util/logger.js";
const STREAM_BUSINESS_TYPE = 10;
/**
 * Manages a single uplink stream session.
 *
 * Usage:
 *   const sender = new WeixinStreamSender(opts);
 *   await sender.init();
 *   await sender.sendPiece({ type: "text", text: "Hello " });
 *   await sender.sendPiece({ type: "text", text: "world!" });
 *   await sender.end();
 */
export class WeixinStreamSender {
    opts;
    deviceId;
    clientStreamId;
    streamTicket;
    pieceSeq = 0;
    ended = false;
    /**
     * Pieces from a previous sendPiece/end call that failed to reach the server.
     * They are prepended to the next syncStream request so the server receives
     * them with the original piece_seq values (true retry, not accumulation).
     */
    pendingPieces = [];
    /** pieceSeq value before the pending pieces were assigned; used for rollback. */
    seqBeforePending = 0;
    constructor(opts) {
        this.opts = opts;
        this.deviceId = getOrCreateDeviceId(opts.accountId);
        this.clientStreamId = `${opts.accountId}:${Date.now()}-${crypto.randomBytes(4).toString("hex")}`;
    }
    /** Call native_init_stream to obtain a stream_ticket. Must be called before sendPiece. */
    async init() {
        let resp;
        try {
            resp = await initStream({
                baseUrl: this.opts.baseUrl,
                token: this.opts.token,
                timeoutMs: this.opts.timeoutMs,
                accountId: this.opts.accountId,
                body: {
                    device_id: this.deviceId,
                    client_stream_id: this.clientStreamId,
                    business_type: STREAM_BUSINESS_TYPE,
                },
            });
        }
        catch (err) {
            logger.warn(`WeixinStreamSender.init: initStream threw streamId=${this.clientStreamId} err=${String(err)}`);
            throw err;
        }
        if (resp.base_response?.ret && resp.base_response.ret !== 0) {
            logger.warn(`WeixinStreamSender.init: ret=${resp.base_response.ret} errmsg=${resp.base_response.errmsg ?? ""} streamId=${this.clientStreamId}`);
            throw new Error(`initStream failed: ret=${resp.base_response.ret} errmsg=${resp.base_response.errmsg ?? ""}`);
        }
        if (!resp.stream_ticket) {
            logger.warn(`WeixinStreamSender.init: no stream_ticket in response streamId=${this.clientStreamId}`);
            throw new Error("initStream: no stream_ticket in response");
        }
        this.streamTicket = resp.stream_ticket;
        logger.debug(`WeixinStreamSender.init: streamId=${this.clientStreamId}`);
    }
    /**
     * Send a single piece of data on the stream.
     * piece_seq auto-increments starting from 1.
     *
     * If a previous call failed, the unsent pieces are automatically prepended
     * to this request so they are retried with their original piece_seq values.
     */
    async sendPiece(data) {
        this.assertReady();
        // Remember the seq checkpoint *before* we assign a new seq, so we can
        // roll back on failure.
        const seqBefore = this.pendingPieces.length > 0
            ? this.seqBeforePending
            : this.pieceSeq;
        this.pieceSeq += 1;
        const newPiece = {
            piece_seq: this.pieceSeq,
            piece_data: Buffer.from(JSON.stringify(data), "utf-8").toString("base64"),
        };
        // Merge any previously-failed pieces with the new one.
        const pieces = [...this.pendingPieces, newPiece];
        try {
            const resp = await syncStream({
                baseUrl: this.opts.baseUrl,
                token: this.opts.token,
                timeoutMs: this.opts.timeoutMs,
                accountId: this.opts.accountId,
                body: {
                    device_id: this.deviceId,
                    client_stream_id: this.clientStreamId,
                    business_type: STREAM_BUSINESS_TYPE,
                    up_piece_list: pieces,
                    end_up_piece_seq: 0,
                },
            });
            this.checkAbort(resp);
            // Success — clear pending state.
            const retried = pieces.length - 1;
            this.pendingPieces = [];
            this.seqBeforePending = 0;
            if (retried > 0) {
                logger.info(`WeixinStreamSender.sendPiece: seq=${this.pieceSeq} type=${data.type} batch=${pieces.length} retried=${retried} streamId=${this.clientStreamId}`);
            }
            else {
                logger.debug(`WeixinStreamSender.sendPiece: seq=${this.pieceSeq} type=${data.type} batch=${pieces.length}`);
            }
            return resp;
        }
        catch (err) {
            // Roll back: save all pieces for retry and restore pieceSeq.
            this.pendingPieces = pieces;
            this.seqBeforePending = seqBefore;
            this.pieceSeq = seqBefore;
            const seqs = pieces.map((p) => p.piece_seq).join(",");
            logger.warn(`WeixinStreamSender.sendPiece: failed — kept pendingSeqs=[${seqs}] rolledBackTo=${seqBefore} type=${data.type} streamId=${this.clientStreamId} err=${String(err)}`);
            throw err;
        }
    }
    /**
     * Signal that the uplink stream has ended.
     * Optionally sends a final piece in the same request as the end marker.
     * Any pending (previously-failed) pieces are included in the same request.
     */
    async end(finalData) {
        this.assertReady();
        this.pieceSeq += 1;
        const finalPiece = {
            piece_seq: this.pieceSeq,
            piece_data: Buffer.from(JSON.stringify(finalData ?? { type: "text", text: "" }), "utf-8").toString("base64"),
        };
        const pieces = [...this.pendingPieces, finalPiece];
        const pendingCarried = this.pendingPieces.length;
        this.ended = true;
        let resp;
        try {
            resp = await syncStream({
                baseUrl: this.opts.baseUrl,
                token: this.opts.token,
                timeoutMs: this.opts.timeoutMs,
                accountId: this.opts.accountId,
                body: {
                    device_id: this.deviceId,
                    client_stream_id: this.clientStreamId,
                    business_type: STREAM_BUSINESS_TYPE,
                    up_piece_list: pieces,
                    end_up_piece_seq: this.pieceSeq,
                },
            });
        }
        catch (err) {
            const seqs = pieces.map((p) => p.piece_seq).join(",");
            logger.warn(`WeixinStreamSender.end: failed — endSeq=${this.pieceSeq} batch=${pieces.length} carriedPending=${pendingCarried} seqs=[${seqs}] streamId=${this.clientStreamId} err=${String(err)}`);
            throw err;
        }
        this.pendingPieces = [];
        this.seqBeforePending = 0;
        if (pendingCarried > 0) {
            logger.info(`WeixinStreamSender.end: endSeq=${this.pieceSeq} batch=${pieces.length} retried=${pendingCarried} streamId=${this.clientStreamId}`);
        }
        else {
            logger.debug(`WeixinStreamSender.end: endSeq=${this.pieceSeq} batch=${pieces.length}`);
        }
        return resp;
    }
    /**
     * Send a client-side abort signal.
     */
    async abort(errorMsg) {
        this.assertReady();
        this.ended = true;
        let resp;
        try {
            resp = await syncStream({
                baseUrl: this.opts.baseUrl,
                token: this.opts.token,
                timeoutMs: this.opts.timeoutMs,
                accountId: this.opts.accountId,
                body: {
                    device_id: this.deviceId,
                    client_stream_id: this.clientStreamId,
                    business_type: STREAM_BUSINESS_TYPE,
                    up_piece_list: [],
                    end_up_piece_seq: this.pieceSeq || 1,
                    abort_info: {
                        abort_type: AbortType.CLIENT_ABORT,
                        abort_detail_error_code: 0,
                        abort_detail_error_msg: errorMsg ?? "client abort",
                    },
                },
            });
        }
        catch (err) {
            logger.warn(`WeixinStreamSender.abort: failed streamId=${this.clientStreamId} reason=${errorMsg ?? "client abort"} err=${String(err)}`);
            throw err;
        }
        logger.debug(`WeixinStreamSender.abort: streamId=${this.clientStreamId} reason=${errorMsg ?? "client abort"}`);
        return resp;
    }
    get currentPieceSeq() {
        return this.pieceSeq;
    }
    get streamId() {
        return this.clientStreamId;
    }
    get ticket() {
        return this.streamTicket;
    }
    get isEnded() {
        return this.ended;
    }
    assertReady() {
        if (!this.streamTicket) {
            throw new Error("WeixinStreamSender: not initialized — call init() first");
        }
        if (this.ended) {
            throw new Error("WeixinStreamSender: stream already ended");
        }
    }
    checkAbort(resp) {
        if (resp.abort_info?.abort_type) {
            const info = resp.abort_info;
            logger.warn(`WeixinStreamSender: server abort type=${info.abort_type} code=${info.abort_detail_error_code} msg=${info.abort_detail_error_msg}`);
            this.ended = true;
            throw new Error(`Stream aborted: type=${info.abort_type} code=${info.abort_detail_error_code} msg=${info.abort_detail_error_msg ?? ""}`);
        }
        if (resp.base_response?.ret && resp.base_response.ret !== 0) {
            logger.warn(`WeixinStreamSender: syncStream error ret=${resp.base_response.ret} errmsg=${resp.base_response.errmsg}`);
            throw new Error(`syncStream failed: ret=${resp.base_response.ret} errmsg=${resp.base_response.errmsg ?? ""}`);
        }
    }
}
//# sourceMappingURL=stream.js.map