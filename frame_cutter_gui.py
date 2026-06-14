import os
import tkinter as tk
from collections import deque
from statistics import median
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

from PIL import Image, ImageTk
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
    DND_AVAILABLE = True
except Exception:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False


Component = Tuple[int, int, int, int, int]  # min_x, min_y, max_x, max_y, pixel_count


class FrameCutterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PNG 帧序列切割工具")
        self.root.geometry("1240x780")
        self.root.minsize(1120, 700)

        self.image_paths: List[str] = []
        self.current_image_index = -1
        self.output_dir = ""
        self.bg_output_dir = ""

        self.source_image: Optional[Image.Image] = None
        self.preview_frames: List[Image.Image] = []
        self.main_preview_photo: Optional[ImageTk.PhotoImage] = None

        self.rows_var = tk.StringVar(value="1")
        self.cols_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="就绪")
        self.pad_width_var = tk.StringVar(value="2")
        self.fps_var = tk.StringVar(value="12")
        self.export_mode_var = tk.StringVar(value="frames")

        self.remove_bg_var = tk.BooleanVar(value=True)
        self.auto_subfolder_var = tk.BooleanVar(value=True)

        self.playing = False
        self.play_after_id: Optional[str] = None
        self.play_index = 0

        self._build_ui()

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=12)
        root_frame.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(root_frame)
        top_bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(top_bar, text="帧序列自动切割工具").pack(side=tk.LEFT)
        ttk.Button(top_bar, text="最小化", command=self._minimize).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(top_bar, text="关闭", command=self.root.destroy).pack(side=tk.RIGHT)

        control_card = ttk.LabelFrame(root_frame, text="参数与操作", padding=12)
        control_card.pack(fill=tk.X, pady=(0, 10))

        row1 = ttk.Frame(control_card)
        row1.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(row1, text="添加图片", command=self._pick_images).pack(side=tk.LEFT)
        ttk.Button(row1, text="移除选中", command=self._remove_selected_image).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row1, text="清空列表", command=self._clear_images).pack(side=tk.LEFT, padx=(8, 0))

        row2 = ttk.Frame(control_card)
        row2.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(row2, text="选择帧切割输出文件夹", command=self._pick_output_dir).pack(side=tk.LEFT)
        self.output_label = ttk.Label(row2, text="未选择帧切割输出文件夹")
        self.output_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)

        row3 = ttk.Frame(control_card)
        row3.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(row3, text="选择去背景输出文件夹", command=self._pick_bg_output_dir).pack(side=tk.LEFT)
        self.bg_output_label = ttk.Label(row3, text="未选择去背景输出文件夹")
        self.bg_output_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)

        row4 = ttk.Frame(control_card)
        row4.pack(fill=tk.X)
        ttk.Label(row4, text="导出功能:").pack(side=tk.LEFT)
        ttk.Radiobutton(row4, text="帧切割", variable=self.export_mode_var, value="frames", command=self._generate_preview).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Radiobutton(row4, text="纯色背景转透明", variable=self.export_mode_var, value="bg", command=self._generate_preview).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Checkbutton(row4, text="帧切割时去背景", variable=self.remove_bg_var, onvalue=True, offvalue=False).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Checkbutton(row4, text="每张图单独子文件夹", variable=self.auto_subfolder_var, onvalue=True, offvalue=False).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(row4, text="序号位数:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Entry(row4, textvariable=self.pad_width_var, width=6).pack(side=tk.LEFT)

        ttk.Button(row4, text="刷新预览", command=self._generate_preview).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(row4, text="开始导出", command=self._export_frames).pack(side=tk.RIGHT)

        grid_row = ttk.Frame(control_card)
        grid_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(grid_row, text="检测到行:").pack(side=tk.LEFT)
        ttk.Entry(grid_row, textvariable=self.rows_var, width=6, state="readonly").pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(grid_row, text="检测到列:").pack(side=tk.LEFT)
        ttk.Entry(grid_row, textvariable=self.cols_var, width=6, state="readonly").pack(side=tk.LEFT, padx=(4, 12))

        preview_card = ttk.LabelFrame(root_frame, text="预览窗口", padding=10)
        preview_card.pack(fill=tk.BOTH, expand=True)

        preview_body = ttk.Frame(preview_card)
        preview_body.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(preview_body)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.main_preview = ttk.Label(left_panel, text="预览区域")
        self.main_preview.pack(fill=tk.BOTH, expand=True)

        play_bar = ttk.Frame(left_panel)
        play_bar.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(play_bar, text="上一帧", command=self._show_prev_frame).pack(side=tk.LEFT)
        ttk.Button(play_bar, text="下一帧", command=self._show_next_frame).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(play_bar, text="播放/暂停", command=self._toggle_play).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(play_bar, text="FPS:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Entry(play_bar, textvariable=self.fps_var, width=6).pack(side=tk.LEFT)

        right_panel = ttk.Frame(preview_body, width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)

        ttk.Label(right_panel, text="待处理图片列表").pack(anchor=tk.W)
        img_list_wrap = ttk.Frame(right_panel)
        img_list_wrap.pack(fill=tk.BOTH, expand=True, pady=(6, 8))

        self.image_list = tk.Listbox(img_list_wrap, height=10, exportselection=False)
        self.image_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_list.bind("<<ListboxSelect>>", self._on_image_select)
        self.image_list.bind("<Delete>", self._on_delete_key_remove_selected)

        image_scroll = ttk.Scrollbar(img_list_wrap, orient=tk.VERTICAL, command=self.image_list.yview)
        image_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_list.config(yscrollcommand=image_scroll.set)
        ttk.Button(right_panel, text="清除选中", command=self._remove_selected_image).pack(anchor=tk.E, pady=(0, 8))

        ttk.Label(right_panel, text="当前图片帧列表").pack(anchor=tk.W)
        frame_list_wrap = ttk.Frame(right_panel)
        frame_list_wrap.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.frame_list = tk.Listbox(frame_list_wrap)
        self.frame_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.frame_list.bind("<<ListboxSelect>>", self._on_frame_select)

        frame_scroll = ttk.Scrollbar(frame_list_wrap, orient=tk.VERTICAL, command=self.frame_list.yview)
        frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_list.config(yscrollcommand=frame_scroll.set)

        progress_row = ttk.Frame(root_frame)
        progress_row.pack(fill=tk.X, pady=(8, 0))
        self.progress = ttk.Progressbar(progress_row, mode="determinate")
        self.progress.pack(fill=tk.X, side=tk.LEFT, expand=True)

        status_bar = ttk.Label(root_frame, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(6, 0))
        self._setup_drag_drop()

    def _minimize(self) -> None:
        self.root.iconify()

    def _pick_images(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择PNG帧序列图",
            filetypes=[("PNG 文件", "*.png"), ("所有文件", "*.*")],
        )
        if not paths:
            return

        self._add_images_and_refresh(list(paths), prefer_last=True)

    def _setup_drag_drop(self) -> None:
        if not DND_AVAILABLE:
            self.status_var.set("就绪（安装 tkinterdnd2 可开启拖拽导入）")
            return
        try:
            self.root.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self.root.dnd_bind("<<Drop>>", self._on_drop_files)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _parse_drop_paths(self, raw: str) -> List[str]:
        paths: List[str] = []
        token = ""
        in_brace = False
        for ch in raw.strip():
            if ch == "{":
                in_brace = True
                token = ""
                continue
            if ch == "}":
                in_brace = False
                if token:
                    paths.append(token)
                token = ""
                continue
            if in_brace:
                token += ch
            elif ch.isspace():
                if token:
                    paths.append(token)
                    token = ""
            else:
                token += ch
        if token:
            paths.append(token)
        return [p for p in paths if p]

    def _on_drop_files(self, event: tk.Event) -> None:
        raw = getattr(event, "data", "") or ""
        candidates = self._parse_drop_paths(str(raw))
        png_paths = [p for p in candidates if os.path.isfile(p) and p.lower().endswith(".png")]
        if not png_paths:
            self.status_var.set("拖拽未识别到 PNG 文件")
            return
        self._add_images_and_refresh(png_paths, prefer_last=True)

    def _add_images_and_refresh(self, paths: List[str], prefer_last: bool = False) -> None:
        added = 0
        last_added_index = -1
        for path in paths:
            if path not in self.image_paths:
                self.image_paths.append(path)
                added += 1
                last_added_index = len(self.image_paths) - 1

        if added == 0:
            self.status_var.set("未添加新图片（可能已在列表中）")
            return

        self._refresh_image_list()
        if prefer_last and last_added_index >= 0:
            self._load_image_by_index(last_added_index)
        elif self.current_image_index < 0 and self.image_paths:
            self._load_image_by_index(0)
        self.status_var.set(f"已添加 {added} 张图片，当前队列共 {len(self.image_paths)} 张")

    def _remove_selected_image(self) -> None:
        selected = self.image_list.curselection()
        if selected:
            idx = int(selected[0])
        elif 0 <= self.current_image_index < len(self.image_paths):
            idx = self.current_image_index
        else:
            return
        del self.image_paths[idx]

        if not self.image_paths:
            self.current_image_index = -1
            self.source_image = None
            self.preview_frames = []
            self._refresh_image_list()
            self.frame_list.delete(0, tk.END)
            self.main_preview.config(image="", text="预览区域")
            self.rows_var.set("1")
            self.cols_var.set("1")
            self.status_var.set("图片列表已空")
            return

        new_idx = max(0, idx - 1)
        self._refresh_image_list()
        self._load_image_by_index(new_idx)

    def _clear_images(self) -> None:
        self.image_paths.clear()
        self.current_image_index = -1
        self.source_image = None
        self.preview_frames = []
        self._refresh_image_list()
        self.frame_list.delete(0, tk.END)
        self.main_preview.config(image="", text="预览区域")
        self.rows_var.set("1")
        self.cols_var.set("1")
        self.status_var.set("已清空图片列表")

    def _refresh_image_list(self) -> None:
        self.image_list.delete(0, tk.END)
        for path in self.image_paths:
            self.image_list.insert(tk.END, os.path.basename(path))

    def _on_image_select(self, _event: tk.Event) -> None:
        selected = self.image_list.curselection()
        if not selected:
            return
        self._load_image_by_index(int(selected[0]))

    def _on_delete_key_remove_selected(self, _event: tk.Event) -> str:
        self._remove_selected_image()
        return "break"

    def _load_image_by_index(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.image_paths):
            return

        path = self.image_paths[idx]
        try:
            image = Image.open(path).convert("RGBA")
        except Exception as exc:
            messagebox.showerror("读取失败", f"无法读取图片:\n{path}\n\n{exc}")
            return

        self.current_image_index = idx
        self.source_image = image
        self.image_list.selection_clear(0, tk.END)
        self.image_list.selection_set(idx)
        self.image_list.activate(idx)

        self.status_var.set(f"已加载: {os.path.basename(path)} ({image.width}x{image.height})")
        self._generate_preview()

    def _pick_output_dir(self) -> None:
        path = filedialog.askdirectory(title="选择输出文件夹")
        if not path:
            return
        self.output_dir = path
        self.output_label.config(text=path)
        self.status_var.set(f"已选择帧切割输出目录: {path}")

    def _pick_bg_output_dir(self) -> None:
        path = filedialog.askdirectory(title="选择去背景输出文件夹")
        if not path:
            return
        self.bg_output_dir = path
        self.bg_output_label.config(text=path)
        self.status_var.set(f"已选择去背景输出目录: {path}")

    def _get_pad_width(self) -> Optional[int]:
        try:
            width = int(self.pad_width_var.get().strip())
        except ValueError:
            messagebox.showerror("参数错误", "序号位数必须是整数。")
            return None
        if width <= 0:
            messagebox.showerror("参数错误", "序号位数必须大于0。")
            return None
        return width

    def _generate_preview(self) -> None:
        if self.source_image is None:
            return

        if self.export_mode_var.get() == "bg":
            frame = self._make_background_transparent(self.source_image)
            self.preview_frames = [frame]
            self.rows_var.set("1")
            self.cols_var.set("1")
        else:
            frames, rows, cols = self._extract_frames_auto(self.source_image)
            self.preview_frames = frames
            self.rows_var.set(str(rows))
            self.cols_var.set(str(cols))

        self.frame_list.delete(0, tk.END)
        if not self.preview_frames:
            self.main_preview.config(image="", text="没有可预览帧")
            self.status_var.set("预览为空：未识别到有效帧")
            return

        for i in range(len(self.preview_frames)):
            self.frame_list.insert(tk.END, f"第 {i + 1} 帧")

        self.play_index = 0
        self.frame_list.selection_set(0)
        self._show_frame(0)
        if self.export_mode_var.get() == "bg":
            self.status_var.set("预览完成：纯色背景转透明模式")
        else:
            self.status_var.set(f"预览完成：识别 {rows} 行 x {cols} 列，共 {len(self.preview_frames)} 帧")

    def _choose_mode_auto(self, image: Image.Image) -> str:
        alpha = image.getchannel("A")
        hist = alpha.histogram()
        total = image.width * image.height
        transparent_like = hist[0] + sum(hist[1:255])
        if transparent_like > total * 0.03:
            return "alpha"
        return "color"

    def _extract_frames_auto(self, image: Image.Image) -> Tuple[List[Image.Image], int, int]:
        mode = self._choose_mode_auto(image)
        components, bg_color = self._detect_components(image, mode)
        if not components:
            return [], 1, 1
        components = self._merge_fragment_components(components)

        ordered_rows = self._group_components_by_rows(components)
        ordered_components: List[Component] = []
        cols = 1
        for row in ordered_rows:
            row_sorted = sorted(row, key=lambda c: (c[0] + c[2]) / 2.0)
            ordered_components.extend(row_sorted)
            cols = max(cols, len(row_sorted))
        rows = max(1, len(ordered_rows))

        widths = [c[2] - c[0] + 1 for c in ordered_components]
        heights = [c[3] - c[1] + 1 for c in ordered_components]
        canvas_w = max(widths) + 6
        canvas_h = max(heights) + 6

        frames: List[Image.Image] = []
        for comp in ordered_components:
            frame = self._extract_component_frame(image, comp, canvas_w, canvas_h, margin=2)
            if self.remove_bg_var.get() and mode == "color" and bg_color is not None:
                frame = self._remove_bg_to_transparent(frame, bg_color)
            frames.append(frame)

        return frames, rows, cols

    def _detect_components(self, image: Image.Image, mode: str) -> Tuple[List[Component], Optional[Tuple[int, int, int]]]:
        width, height = image.size
        px = image.load()
        visited = bytearray(width * height)
        bg_color = self._estimate_background_color(image) if mode == "color" else None

        min_component_pixels = max(120, (width * height) // 5000)
        min_box_w = max(8, width // 70)
        min_box_h = max(8, height // 28)

        components: List[Component] = []

        def idx(x: int, y: int) -> int:
            return y * width + x

        for y in range(height):
            for x in range(width):
                p = idx(x, y)
                if visited[p]:
                    continue
                visited[p] = 1

                if not self._is_foreground_by_mode(px[x, y], mode, bg_color):
                    continue

                q: deque[Tuple[int, int]] = deque()
                q.append((x, y))
                cnt = 0
                min_x = max_x = x
                min_y = max_y = y

                while q:
                    cx, cy = q.popleft()
                    cnt += 1
                    if cx < min_x:
                        min_x = cx
                    if cx > max_x:
                        max_x = cx
                    if cy < min_y:
                        min_y = cy
                    if cy > max_y:
                        max_y = cy

                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if nx < 0 or ny < 0 or nx >= width or ny >= height:
                            continue
                        np = idx(nx, ny)
                        if visited[np]:
                            continue
                        visited[np] = 1
                        if self._is_foreground_by_mode(px[nx, ny], mode, bg_color):
                            q.append((nx, ny))

                box_w = max_x - min_x + 1
                box_h = max_y - min_y + 1
                if cnt >= min_component_pixels and box_w >= min_box_w and box_h >= min_box_h:
                    components.append((min_x, min_y, max_x, max_y, cnt))

        if not components:
            return [], bg_color

        areas = sorted(c[4] for c in components)
        med_area = median(areas)
        area_floor = max(min_component_pixels, int(med_area * 0.25))
        filtered = [c for c in components if c[4] >= area_floor]

        return filtered, bg_color

    def _merge_fragment_components(self, components: List[Component]) -> List[Component]:
        if not components:
            return []
        if len(components) <= 1:
            return components

        areas = sorted(c[4] for c in components)
        med_area = median(areas)
        main_floor = max(80, int(med_area * 0.5))

        main_components = [c for c in components if c[4] >= main_floor]
        tiny_components = [c for c in components if c[4] < main_floor]
        if not main_components:
            return components
        if not tiny_components:
            return main_components

        merged = main_components[:]
        widths = [c[2] - c[0] + 1 for c in main_components]
        heights = [c[3] - c[1] + 1 for c in main_components]
        gap_limit_x = max(8.0, median(widths) * 0.45)
        gap_limit_y = max(8.0, median(heights) * 0.35)
        center_limit = max(16.0, median(widths) * 0.95)

        def overlap_len(a1: int, a2: int, b1: int, b2: int) -> int:
            return max(0, min(a2, b2) - max(a1, b1) + 1)

        for frag in tiny_components:
            best_i = -1
            best_score = 10**9
            fx1, fy1, fx2, fy2, fcnt = frag
            fcx = (fx1 + fx2) / 2.0
            fcy = (fy1 + fy2) / 2.0

            for i, base in enumerate(merged):
                bx1, by1, bx2, by2, bcnt = base
                bcx = (bx1 + bx2) / 2.0
                bcy = (by1 + by2) / 2.0
                x_gap = max(0.0, max(bx1 - fx2 - 1, fx1 - bx2 - 1))
                y_gap = max(0.0, max(by1 - fy2 - 1, fy1 - by2 - 1))
                y_overlap = overlap_len(fy1, fy2, by1, by2)
                min_h = max(1, min(fy2 - fy1 + 1, by2 - by1 + 1))
                overlap_ratio = y_overlap / float(min_h)

                close_enough = (x_gap <= gap_limit_x and y_gap <= gap_limit_y) or overlap_ratio >= 0.25
                if not close_enough:
                    continue

                score = abs(fcx - bcx) + abs(fcy - bcy) + x_gap * 1.5 + y_gap * 2.0
                if abs(fcx - bcx) > center_limit:
                    continue
                if score < best_score:
                    best_score = score
                    best_i = i

            if best_i >= 0:
                bx1, by1, bx2, by2, bcnt = merged[best_i]
                merged[best_i] = (
                    min(bx1, fx1),
                    min(by1, fy1),
                    max(bx2, fx2),
                    max(by2, fy2),
                    bcnt + fcnt,
                )

        return merged

    def _is_foreground_by_mode(self, pixel: Tuple[int, int, int, int], mode: str, bg_color: Optional[Tuple[int, int, int]]) -> bool:
        if mode == "alpha":
            return pixel[3] > 8
        if bg_color is None:
            return pixel[3] > 8
        return self._is_foreground_pixel(pixel, bg_color[0], bg_color[1], bg_color[2])

    def _group_components_by_rows(self, components: List[Component]) -> List[List[Component]]:
        if not components:
            return []

        heights = [c[3] - c[1] + 1 for c in components]
        tol_y = max(18.0, median(heights) * 0.55)

        comps_sorted = sorted(components, key=lambda c: ((c[1] + c[3]) / 2.0, (c[0] + c[2]) / 2.0))
        rows: List[List[Component]] = []
        centers: List[float] = []

        for comp in comps_sorted:
            y_center = (comp[1] + comp[3]) / 2.0
            placed = False
            for i, cy in enumerate(centers):
                if abs(y_center - cy) <= tol_y:
                    rows[i].append(comp)
                    centers[i] = (centers[i] + y_center) / 2.0
                    placed = True
                    break
            if not placed:
                rows.append([comp])
                centers.append(y_center)

        row_pairs = sorted(zip(centers, rows), key=lambda p: p[0])
        return [r for _, r in row_pairs]

    def _extract_component_frame(
        self,
        image: Image.Image,
        comp: Component,
        canvas_w: int,
        canvas_h: int,
        margin: int = 2,
    ) -> Image.Image:
        width, height = image.size
        x1, y1, x2, y2, _ = comp
        crop_left = max(0, x1 - margin)
        crop_top = max(0, y1 - margin)
        crop_right = min(width, x2 + 1 + margin)
        crop_bottom = min(height, y2 + 1 + margin)

        src_crop = image.crop((crop_left, crop_top, crop_right, crop_bottom))
        out = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        paste_x = (canvas_w - src_crop.width) // 2
        paste_y = (canvas_h - src_crop.height) // 2
        out.paste(src_crop, (paste_x, paste_y))
        return out

    @staticmethod
    def _estimate_background_color(image: Image.Image) -> Tuple[int, int, int]:
        width, height = image.size
        px = image.load()
        samples: List[Tuple[int, int, int]] = []

        for x in range(width):
            r, g, b, _ = px[x, 0]
            samples.append((r, g, b))
            r, g, b, _ = px[x, height - 1]
            samples.append((r, g, b))
        for y in range(height):
            r, g, b, _ = px[0, y]
            samples.append((r, g, b))
            r, g, b, _ = px[width - 1, y]
            samples.append((r, g, b))

        rs = sorted(v[0] for v in samples)
        gs = sorted(v[1] for v in samples)
        bs = sorted(v[2] for v in samples)
        mid = len(samples) // 2
        return rs[mid], gs[mid], bs[mid]

    @staticmethod
    def _is_foreground_pixel(pixel: Tuple[int, int, int, int], bg_r: int, bg_g: int, bg_b: int) -> bool:
        r, g, b, a = pixel
        if a <= 8:
            return False
        diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
        if diff >= 42:
            return True
        return a < 250

    def _remove_bg_to_transparent(self, frame: Image.Image, bg_color: Tuple[int, int, int]) -> Image.Image:
        return self._make_background_transparent(frame, bg_color)

    def _make_background_transparent(
        self,
        image: Image.Image,
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> Image.Image:
        out = image.copy().convert("RGBA")
        width, height = out.size
        px = out.load()
        if bg_color is None:
            bg_color = self._estimate_background_color(out)
        bg_r, bg_g, bg_b = bg_color

        visited = bytearray(width * height)
        q: deque[Tuple[int, int]] = deque()

        def idx(x: int, y: int) -> int:
            return y * width + x

        def is_bg_like(pixel: Tuple[int, int, int, int]) -> bool:
            r, g, b, a = pixel
            if a <= 6:
                return True
            diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
            return diff <= 34

        # Start flood-fill from edges only: removes true background, keeps internal details.
        for x in range(width):
            q.append((x, 0))
            q.append((x, height - 1))
        for y in range(height):
            q.append((0, y))
            q.append((width - 1, y))

        while q:
            x, y = q.popleft()
            p = idx(x, y)
            if visited[p]:
                continue
            visited[p] = 1

            if not is_bg_like(px[x, y]):
                continue

            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)

            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                np = idx(nx, ny)
                if not visited[np]:
                    q.append((nx, ny))
        return out

    def _on_frame_select(self, _event: tk.Event) -> None:
        if not self.preview_frames:
            return
        selected = self.frame_list.curselection()
        if not selected:
            return
        self.play_index = int(selected[0])
        self._show_frame(self.play_index)

    def _show_frame(self, idx: int) -> None:
        if not self.preview_frames:
            return

        frame = self.preview_frames[idx]
        max_w, max_h = 780, 580
        scale = min(max_w / frame.width, max_h / frame.height, 1.0)
        size = (max(1, int(frame.width * scale)), max(1, int(frame.height * scale)))
        img = frame.resize(size, Image.Resampling.NEAREST)

        self.main_preview_photo = ImageTk.PhotoImage(img)
        self.main_preview.config(image=self.main_preview_photo, text="")

        self.frame_list.selection_clear(0, tk.END)
        self.frame_list.selection_set(idx)
        self.frame_list.activate(idx)

    def _show_next_frame(self) -> None:
        if not self.preview_frames:
            return
        self.play_index = (self.play_index + 1) % len(self.preview_frames)
        self._show_frame(self.play_index)

    def _show_prev_frame(self) -> None:
        if not self.preview_frames:
            return
        self.play_index = (self.play_index - 1) % len(self.preview_frames)
        self._show_frame(self.play_index)

    def _toggle_play(self) -> None:
        if not self.preview_frames:
            return

        self.playing = not self.playing
        if self.playing:
            self._play_tick()
            self.status_var.set("预览播放中")
        else:
            if self.play_after_id is not None:
                self.root.after_cancel(self.play_after_id)
                self.play_after_id = None
            self.status_var.set("预览已暂停")

    def _play_tick(self) -> None:
        if not self.playing or not self.preview_frames:
            return

        try:
            fps = int(self.fps_var.get().strip())
        except ValueError:
            fps = 12
        fps = max(1, min(60, fps))

        self._show_next_frame()
        self.play_after_id = self.root.after(int(1000 / fps), self._play_tick)

    def _export_frames(self) -> None:
        if not self.image_paths:
            messagebox.showwarning("缺少输入", "请先添加至少一张图片。")
            return

        pad_width = self._get_pad_width()
        if pad_width is None:
            return

        mode = self.export_mode_var.get()
        if mode == "frames":
            if not self.output_dir:
                messagebox.showwarning("缺少输出目录", "请先选择帧切割输出文件夹。")
                return
        else:
            if not self.bg_output_dir:
                messagebox.showwarning("缺少输出目录", "请先选择去背景输出文件夹。")
                return

        total = len(self.image_paths)
        exported = 0
        failed: List[str] = []

        self.progress["maximum"] = total
        self.progress["value"] = 0

        for i, path in enumerate(self.image_paths, start=1):
            try:
                image = Image.open(path).convert("RGBA")
            except Exception:
                failed.append(os.path.basename(path))
                self.progress["value"] = i
                self.root.update_idletasks()
                continue

            base_name = os.path.splitext(os.path.basename(path))[0]
            if mode == "frames":
                frames, rows, cols = self._extract_frames_auto(image)
                if not frames:
                    failed.append(os.path.basename(path))
                    self.progress["value"] = i
                    self.root.update_idletasks()
                    continue

                target_dir = self.output_dir
                if self.auto_subfolder_var.get():
                    target_dir = os.path.join(self.output_dir, base_name)
                    os.makedirs(target_dir, exist_ok=True)

                for index, frame in enumerate(frames, start=1):
                    serial = str(index).zfill(pad_width)
                    out_name = f"{serial}_{base_name}.png"
                    frame.save(os.path.join(target_dir, out_name))
                    exported += 1
                self.status_var.set(f"处理中: {i}/{total} ({base_name}) 识别 {rows}x{cols}")
            else:
                target_dir = self.bg_output_dir
                if self.auto_subfolder_var.get():
                    target_dir = os.path.join(self.bg_output_dir, base_name)
                    os.makedirs(target_dir, exist_ok=True)
                out_img = self._make_background_transparent(image)
                out_name = f"{base_name}_alpha.png"
                out_img.save(os.path.join(target_dir, out_name))
                exported += 1
                self.status_var.set(f"处理中: {i}/{total} ({base_name}) 去背景")

            self.progress["value"] = i
            self.root.update_idletasks()

        if self.current_image_index >= 0:
            self._load_image_by_index(self.current_image_index)

        if failed:
            self.status_var.set(f"导出完成：{exported} 张，失败 {len(failed)} 张源图")
            messagebox.showwarning("导出完成（部分失败）", f"成功导出 {exported} 张。\n失败源图 {len(failed)} 张。")
        else:
            if mode == "frames":
                self.status_var.set(f"导出完成：{exported} 张 -> {self.output_dir}")
            else:
                self.status_var.set(f"导出完成：{exported} 张 -> {self.bg_output_dir}")
            messagebox.showinfo("导出完成", f"成功导出 {exported} 张图片。")


def main() -> None:
    if DND_AVAILABLE and TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    FrameCutterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
