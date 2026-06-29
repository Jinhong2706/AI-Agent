import sys
import numpy as np
from PIL import Image, ImageFilter

REMBG_SESSIONS = {}


def _feather_alpha_edges(img, radius=1.5):
    """Feather alpha edges to reduce jagged appearance in GIF output."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    try:
        arr = np.array(img)
        alpha = arr[:, :, 3].astype(np.float32) / 255.0

        edge_mask = (alpha > 0.05) & (alpha < 0.98)
        if not np.any(edge_mask):
            return img

        try:
            import cv2

            kernel = np.ones((3, 3), np.uint8)
            edge_mask_dilated = cv2.dilate(
                edge_mask.astype(np.uint8), kernel, iterations=1
            )
            blur_region = edge_mask_dilated > 0
        except ImportError:
            blur_region = edge_mask

        alpha_pil = Image.fromarray((alpha * 255).astype(np.uint8), mode="L")
        alpha_blurred = alpha_pil.filter(ImageFilter.GaussianBlur(radius=radius))
        alpha_blurred_arr = np.array(alpha_blurred).astype(np.float32) / 255.0

        final_alpha = alpha.copy()
        final_alpha[blur_region] = alpha_blurred_arr[blur_region]

        final_alpha_pil = Image.fromarray(
            (final_alpha * 255).astype(np.uint8), mode="L"
        )
        final_alpha_pil = final_alpha_pil.filter(ImageFilter.GaussianBlur(radius=0.5))

        arr[:, :, 3] = np.array(final_alpha_pil)
        return Image.fromarray(arr, "RGBA")

    except Exception as e:
        print(f"[*] Edge feathering failed: {e}, returning original", file=sys.stderr)
        return img


def _sharpen_alpha_edges(img, threshold=200):
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    try:
        arr = np.array(img)
        alpha = arr[:, :, 3]

        mask = (alpha > 50) & (alpha < threshold)

        if not np.any(mask):
            return img

        arr[mask, 3] = np.where(alpha[mask] > threshold // 2, 255, 0)

        return Image.fromarray(arr)
    except ImportError:
        return img


def _remove_background_with_rembg(img, model_name="isnet-anime", alpha_matting=True):
    try:
        from rembg import remove, new_session
    except ImportError:
        raise RuntimeError("rembg 未安装，请先执行: pip install rembg")

    session = REMBG_SESSIONS.get(model_name)
    if session is None:
        session = new_session(model_name)
        REMBG_SESSIONS[model_name] = session

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    out_img = remove(img, session=session, alpha_matting=alpha_matting)

    if out_img.mode != "RGBA":
        out_img = out_img.convert("RGBA")
    return out_img


def _remove_background_dual(img, model_name="isnet-anime", alpha_matting=True):
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    original_arr = np.array(img)
    h, w = original_arr.shape[:2]

    alpha_opencv = None
    try:
        from modules.bg_opencv import remove_background_opencv

        opencv_result = remove_background_opencv(img.convert("RGB"))
        if opencv_result.mode == "RGBA":
            alpha_opencv = np.array(opencv_result)[:, :, 3]
    except Exception as e:
        try:
            import cv2

            rgb = np.array(img.convert("RGB"))
            mask = np.zeros((h + 2, w + 2), np.uint8)
            seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
            flags = cv2.FLOODFILL_MASK_ONLY | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE
            for seed in seeds:
                cv2.floodFill(
                    rgb, mask, seed, (255, 255, 255), (15, 15, 15), (15, 15, 15), flags
                )
            bg_mask = mask[1:-1, 1:-1] > 0
            img_norm = rgb.astype(np.float32) / 255.0
            dist_from_white = 1.0 - img_norm.min(axis=2)
            alpha_opencv = np.ones((h, w), dtype=np.float32)
            alpha_opencv[bg_mask] = dist_from_white[bg_mask]
            alpha_opencv[alpha_opencv < (15.0 / 255.0)] = 0.0
            alpha_opencv = (alpha_opencv * 255).astype(np.uint8)
            print(
                "[*] Dual mode: OpenCV fallback (relaxed threshold) succeeded",
                file=sys.stderr,
            )
        except Exception as e2:
            print(
                f"[*] Dual mode: OpenCV failed ({e}, {e2}), will rely on rembg only",
                file=sys.stderr,
            )

    alpha_rembg = None
    try:
        rembg_result = _remove_background_with_rembg(
            img, model_name=model_name, alpha_matting=alpha_matting
        )
        if rembg_result.mode == "RGBA":
            alpha_rembg = np.array(rembg_result)[:, :, 3]
    except Exception as e:
        print(
            f"[*] Dual mode: Rembg failed ({e}), will rely on opencv only",
            file=sys.stderr,
        )

    if alpha_opencv is None and alpha_rembg is None:
        raise RuntimeError("Dual mode: Both OpenCV and Rembg failed")

    if alpha_opencv is None:
        final_alpha = alpha_rembg
    elif alpha_rembg is None:
        final_alpha = alpha_opencv
    else:
        final_alpha = np.maximum(alpha_opencv, alpha_rembg)

    final_arr = original_arr.copy()
    final_arr[:, :, 3] = final_alpha

    return Image.fromarray(final_arr, "RGBA")


def apply_background_removal(img, bg_cfg):
    if not bg_cfg.get("enabled"):
        return img

    method = str(bg_cfg.get("method", "rembg")).strip().lower()
    model_name = bg_cfg.get("model", "isnet-anime")
    alpha_matting = bg_cfg.get("alpha_matting", True)
    feather_edges = bg_cfg.get("feather_edges", True)
    feather_radius = bg_cfg.get("feather_radius", 1.5)
    sharpen_edges = bg_cfg.get("sharpen_edges", False)
    sharpen_threshold = bg_cfg.get("sharpen_threshold", 200)

    try:
        if method == "opencv":
            from modules.bg_opencv import remove_background_opencv

            out = remove_background_opencv(img)
        elif method == "rembg":
            out = _remove_background_with_rembg(
                img, model_name=model_name, alpha_matting=alpha_matting
            )
        elif method == "dual":
            out = _remove_background_dual(
                img, model_name=model_name, alpha_matting=alpha_matting
            )
        else:
            print(
                f"[!] Unknown bg_removal_method={method}, using dual", file=sys.stderr
            )
            out = _remove_background_dual(
                img, model_name=model_name, alpha_matting=alpha_matting
            )

        if out is not None and out.mode == "RGBA":
            arr = np.array(out)
            arr[arr[:, :, 3] < 10, 3] = 0
            out = Image.fromarray(arr)

        if feather_edges:
            out = _feather_alpha_edges(out, radius=feather_radius)

        if sharpen_edges:
            out = _sharpen_alpha_edges(out, threshold=sharpen_threshold)

        return out
    except Exception as e:
        print(f"[!] Background removal failed ({method}): {e}", file=sys.stderr)
        print("[*] Keeping original image for this frame.", file=sys.stderr)
        return img
