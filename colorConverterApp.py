import customtkinter as ctk
from tkinter import Canvas
import math
from PIL import Image, ImageDraw, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ColorConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ColorSpaceConverter")
        self.root.geometry("1100x850")

        self.updating = False
        self.warning_var = ctk.StringVar()

        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)

        left_frame = ctk.CTkFrame(main_container, corner_radius=10)
        left_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, padx=(0, 10))

        right_frame = ctk.CTkFrame(main_container, corner_radius=10, fg_color="transparent")
        right_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        self.create_color_picker(left_frame)
        self.create_color_display(right_frame)
        self.create_rgb_controls(right_frame)
        self.create_lab_controls(right_frame)
        self.create_cmyk_controls(right_frame)
        self.create_warning_label(right_frame)

        self.set_rgb(255, 255, 255)


    def validate_integer_input(self, P):
        if P == "":  
            return True
        if P == "-": 
            return True
        if P.lstrip('-').isdigit():  
            return True
        return False

    def validate_float_input(self, P):
        if P == "" or P == "-" or P == "." or P == "-.":
            return True
        if P.count('.') <= 1:
            try:
                float(P)
                return True
            except ValueError:
                pass
        return False

    def validate_entry_range(self, variable, min_val, max_val):
        try:
            value = variable.get()
            if value < min_val:
                variable.set(min_val)
            elif value > max_val:
                variable.set(max_val)
        except:
            variable.set(min_val)

    def create_color_picker(self, parent):
        title_label = ctk.CTkLabel(parent, text="Палитра", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(15, 10), padx=15)

        self.wheel_size = 300
        self.wheel_canvas = Canvas(parent, width=self.wheel_size,
                                   height=self.wheel_size, bg="#2b2b2b",
                                   highlightthickness=0)
        self.wheel_canvas.pack(pady=10, padx=15)

        self.draw_color_wheel_pil()

        slider_frame = ctk.CTkFrame(parent, fg_color="transparent")
        slider_frame.pack(pady=10, padx=15, fill=ctk.X)

        brightness_label = ctk.CTkLabel(slider_frame, text="Яркость",font=ctk.CTkFont(size=13))
        brightness_label.pack(anchor=ctk.W, pady=(0, 5))

        self.brightness_var = ctk.DoubleVar(value=100)
        self.brightness_slider = ctk.CTkSlider(slider_frame, from_=0, to=100,
                                               variable=self.brightness_var,
                                               width=280,
                                               command=self.on_brightness_change)
        self.brightness_slider.pack(fill=ctk.X)

        self.brightness_value_label = ctk.CTkLabel(slider_frame, text="100", 
                                                   font=ctk.CTkFont(size=12))
        self.brightness_value_label.pack(pady=(5, 10))

        self.wheel_canvas.bind("<Button-1>", self.on_wheel_click)
        self.wheel_canvas.bind("<B1-Motion>", self.on_wheel_drag)

        self.selection_indicator_ids = []
        self.current_h = 0
        self.current_s = 0
        self.current_v = 100

    def draw_color_wheel_pil(self):
        img = Image.new('RGB', (self.wheel_size, self.wheel_size), '#2b2b2b')
        draw = ImageDraw.Draw(img)

        center = self.wheel_size // 2
        radius = (self.wheel_size - 20) // 2

        for x in range(self.wheel_size):
            for y in range(self.wheel_size):
                dx = x - center
                dy = y - center
                distance = math.sqrt(dx*dx + dy*dy)

                if distance <= radius:
                    angle = math.atan2(dy, dx)
                    hue = (math.degrees(angle) + 180) % 360
                    saturation = (distance / radius) * 100
                    value = 100

                    r, g, b = self.hsv_to_rgb(hue, saturation, value)
                    img.putpixel((x, y), (r, g, b))

        center_radius = 15
        draw.ellipse([center - center_radius, center - center_radius,
                     center + center_radius, center + center_radius],
                    fill='white', outline='gray', width=2)

        draw.ellipse([10, 10, self.wheel_size-10, self.wheel_size-10],
                    outline='#1f538d', width=3)

        self.wheel_image = ImageTk.PhotoImage(img)
        self.wheel_canvas.create_image(0, 0, anchor=ctk.NW, image=self.wheel_image)

    def on_wheel_click(self, event):
        self.update_color_from_wheel(event.x, event.y)

    def on_wheel_drag(self, event):
        self.update_color_from_wheel(event.x, event.y)

    def update_color_from_wheel(self, x, y):
        center = self.wheel_size // 2
        radius = (self.wheel_size - 20) // 2
        dx = x - center
        dy = y - center
        distance = math.sqrt(dx*dx + dy*dy)

        if distance <= radius:
            angle = math.atan2(dy, dx)
            self.current_h = (math.degrees(angle) + 180) % 360
            self.current_s = min(100, (distance / radius) * 100)
            self.current_v = self.brightness_var.get()

            self.draw_selection_indicator(x, y)

            r, g, b = self.hsv_to_rgb(self.current_h, self.current_s, self.current_v)
            self.set_rgb(r, g, b)

    def update_wheel_marker_from_hsv(self):
        center = self.wheel_size // 2
        radius = (self.wheel_size - 20) // 2

        angle_rad = math.radians((self.current_h - 180) % 360)
        distance = (self.current_s / 100.0) * radius

        x = center + distance * math.cos(angle_rad)
        y = center + distance * math.sin(angle_rad)

        self.draw_selection_indicator(int(x), int(y))

    def draw_selection_indicator(self, x, y):
        for item_id in self.selection_indicator_ids:
            self.wheel_canvas.delete(item_id)
        self.selection_indicator_ids.clear()

        radius = 8
        outer = self.wheel_canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline="white", width=3
        )
        inner = self.wheel_canvas.create_oval(
            x - radius + 2, y - radius + 2,
            x + radius - 2, y + radius - 2,
            outline="black", width=2
        )

        self.selection_indicator_ids = [outer, inner]

    def on_brightness_change(self, value):
        if self.updating:
            return
        self.current_v = float(value)
        self.brightness_value_label.configure(text=f"{int(value)}")
        r, g, b = self.hsv_to_rgb(self.current_h, self.current_s, self.current_v)
        self.set_rgb(r, g, b)

    def create_color_display(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(pady=(0, 10), padx=10, fill=ctk.X)

        title_label = ctk.CTkLabel(frame, text="цвет", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=(10, 5))

        self.color_canvas = Canvas(frame, width=220, height=90, 
                                   bg="white", highlightthickness=0)
        self.color_canvas.pack(pady=(5, 15), padx=15)

    def create_rgb_controls(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(pady=5, padx=10, fill=ctk.X)

        title_label = ctk.CTkLabel(frame, text="RGB", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=(10, 10), padx=10)

        self.r_var = ctk.IntVar(value=255)
        self.g_var = ctk.IntVar(value=255)
        self.b_var = ctk.IntVar(value=255)

        self.create_slider_group(frame, "R", self.r_var, "#e74c3c", 0, 0, 255)
        self.create_slider_group(frame, "G", self.g_var, "#2ecc71", 1, 0, 255)
        self.create_slider_group(frame, "B", self.b_var, "#3498db", 2, 0, 255)

    def create_lab_controls(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(pady=5, padx=10, fill=ctk.X)

        title_label = ctk.CTkLabel(frame, text="LAB",
                                   font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=(10, 10), padx=10)

        self.l_var = ctk.DoubleVar(value=100)
        self.a_var = ctk.DoubleVar(value=0)
        self.b_var_lab = ctk.DoubleVar(value=0)

        self.create_slider_group(frame, "L", self.l_var, "#636363", 0, 0, 100, is_lab=True)
        self.create_slider_group(frame, "A", self.a_var, "#636363", 1, -128, 127, is_lab=True)
        self.create_slider_group(frame, "B", self.b_var_lab, "#636363", 2, -128, 127, is_lab=True)

    def create_cmyk_controls(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(pady=5, padx=10, fill=ctk.X)

        title_label = ctk.CTkLabel(frame, text="CMYK", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=(10, 10), padx=10)

        self.c_var = ctk.DoubleVar(value=0)
        self.m_var = ctk.DoubleVar(value=0)
        self.y_var = ctk.DoubleVar(value=0)
        self.k_var = ctk.DoubleVar(value=0)

        self.create_slider_group(frame, "C", self.c_var, "#636363", 0, 0, 100, is_cmyk=True)
        self.create_slider_group(frame, "M", self.m_var, "#636363", 1, 0, 100, is_cmyk=True)
        self.create_slider_group(frame, "Y", self.y_var, "#636363", 2, 0, 100, is_cmyk=True)
        self.create_slider_group(frame, "K", self.k_var, "#636363", 3, 0, 100, is_cmyk=True)

    def create_slider_group(self, parent, label_text, variable, color, row,
                           from_=0, to=255, is_lab=False, is_cmyk=False):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(pady=5, padx=15, fill=ctk.X)

        label = ctk.CTkLabel(container, text=label_text, width=30,
                            font=ctk.CTkFont(size=13, weight="bold"))
        label.pack(side=ctk.LEFT, padx=(0, 10))

        if is_lab or is_cmyk:
            vcmd = (self.root.register(self.validate_float_input), '%P')
        else:
            vcmd = (self.root.register(self.validate_integer_input), '%P')


        entry = ctk.CTkEntry(container, textvariable=variable, width=70, font=ctk.CTkFont(size=12))
        entry.pack(side=ctk.LEFT, padx=(0, 10))

        entry._entry.configure(validate="key", validatecommand=vcmd)

        entry.bind("<FocusOut>", lambda e: self.validate_entry_range(variable, from_, to))
        entry.bind("<Return>", lambda e: self.validate_entry_range(variable, from_, to))

        slider = ctk.CTkSlider(container, from_=from_, to=to,
                              variable=variable, width=200,
                              button_color=color,
                              button_hover_color=color)
        slider.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        if is_lab:
            variable.trace_add("write", lambda *args: self.on_lab_change())
        elif is_cmyk:
            variable.trace_add("write", lambda *args: self.on_cmyk_change())
        else:
            variable.trace_add("write", lambda *args: self.on_rgb_change())

    def create_warning_label(self, parent):
        self.warning_label = ctk.CTkLabel(parent, textvariable=self.warning_var,
                                         text_color="#ff9800",
                                         font=ctk.CTkFont(size=11, slant="italic"))
        self.warning_label.pack(pady=10)

    def on_rgb_change(self):
        if self.updating:
            return
        self.updating = True
        try:
            r = max(0, min(255, int(self.r_var.get())))
            g = max(0, min(255, int(self.g_var.get())))
            b = max(0, min(255, int(self.b_var.get())))

            if self.r_var.get() != r:
                self.r_var.set(r)
            if self.g_var.get() != g:
                self.g_var.set(g)
            if self.b_var.get() != b:
                self.b_var.set(b)

            self.update_color_display(r, g, b)
            self.update_hsv_from_rgb(r, g, b)
            self.update_wheel_marker_from_hsv()

            L, a, b_lab = self.rgb_to_lab(r, g, b)
            self.l_var.set(round(L, 2))
            self.a_var.set(round(a, 2))
            self.b_var_lab.set(round(b_lab, 2))

            c, m, y, k = self.rgb_to_cmyk(r, g, b)
            self.c_var.set(round(c, 2))
            self.m_var.set(round(m, 2))
            self.y_var.set(round(y, 2))
            self.k_var.set(round(k, 2))

            self.warning_var.set("")
        finally:
            self.updating = False

    def on_lab_change(self):
        if self.updating:
            return
        self.updating = True
        try:
            L = max(0.0, min(100.0, float(self.l_var.get())))
            a = max(-128.0, min(127.0, float(self.a_var.get())))
            b_lab = max(-128.0, min(127.0, float(self.b_var_lab.get())))

            if self.l_var.get() != L:
                self.l_var.set(L)
            if self.a_var.get() != a:
                self.a_var.set(a)
            if self.b_var_lab.get() != b_lab:
                self.b_var_lab.set(b_lab)

            r, g, b, clipped = self.lab_to_rgb(L, a, b_lab)

            if clipped:
                self.warning_var.set("RGB значения обрезаны")
            else:
                self.warning_var.set("")

            self.r_var.set(r)
            self.g_var.set(g)
            self.b_var.set(b)

            self.update_color_display(r, g, b)
            self.update_hsv_from_rgb(r, g, b)
            self.update_wheel_marker_from_hsv()

            c, m, y, k = self.rgb_to_cmyk(r, g, b)
            self.c_var.set(round(c, 2))
            self.m_var.set(round(m, 2))
            self.y_var.set(round(y, 2))
            self.k_var.set(round(k, 2))
        finally:
            self.updating = False

    def on_cmyk_change(self):
        if self.updating:
            return
        self.updating = True
        try:
            c = max(0, min(100, float(self.c_var.get())))
            m = max(0, min(100, float(self.m_var.get())))
            y = max(0, min(100, float(self.y_var.get())))
            k = max(0, min(100, float(self.k_var.get())))

            r, g, b = self.cmyk_to_rgb(c, m, y, k)

            self.r_var.set(r)
            self.g_var.set(g)
            self.b_var.set(b)

            self.update_color_display(r, g, b)
            self.update_hsv_from_rgb(r, g, b)
            self.update_wheel_marker_from_hsv()

            L, a, b_lab = self.rgb_to_lab(r, g, b)
            self.l_var.set(round(L, 2))
            self.a_var.set(round(a, 2))
            self.b_var_lab.set(round(b_lab, 2))

            self.warning_var.set("")
        finally:
            self.updating = False

    def update_hsv_from_rgb(self, r, g, b):
        h, s, v = self.rgb_to_hsv(r, g, b)
        self.current_h = h
        self.current_s = s
        self.current_v = v
        self.brightness_var.set(v)

    def update_color_display(self, r, g, b):
        color_hex = f"#{r:02x}{g:02x}{b:02x}"
        self.color_canvas.configure(bg=color_hex)

    def set_rgb(self, r, g, b):
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)


    def hsv_to_rgb(self, h, s, v):
        h = h / 360.0
        s = s / 100.0
        v = v / 100.0
        if s == 0:
            r = g = b = v
        else:
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6
            if i == 0: r, g, b = v, t, p
            elif i == 1: r, g, b = q, v, p
            elif i == 2: r, g, b = p, v, t
            elif i == 3: r, g, b = p, q, v
            elif i == 4: r, g, b = t, p, v
            else: r, g, b = v, p, q
        return int(r * 255), int(g * 255), int(b * 255)

    def rgb_to_hsv(self, r, g, b):
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        diff = max_c - min_c
        if diff == 0:
            h = 0
        elif max_c == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_c == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360
        s = 0 if max_c == 0 else (diff / max_c) * 100
        v = max_c * 100
        return h, s, v

    def rgb_to_cmyk(self, r, g, b):
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0
        k = 1 - max(r_norm, g_norm, b_norm)
        if k == 1:
            return 0, 0, 0, 100
        c = (1 - r_norm - k) / (1 - k)
        m = (1 - g_norm - k) / (1 - k)
        y = (1 - b_norm - k) / (1 - k)
        return c * 100, m * 100, y * 100, k * 100

    def cmyk_to_rgb(self, c, m, y, k):
        c_norm = c / 100.0
        m_norm = m / 100.0
        y_norm = y / 100.0
        k_norm = k / 100.0
        r = 255 * (1 - c_norm) * (1 - k_norm)
        g = 255 * (1 - m_norm) * (1 - k_norm)
        b = 255 * (1 - y_norm) * (1 - k_norm)
        return int(round(r)), int(round(g)), int(round(b))

    def rgb_to_lab(self, r, g, b):
        X, Y, Z = self.rgb_to_xyz(r, g, b)
        L, a, b_lab = self.xyz_to_lab(X, Y, Z)
        return L, a, b_lab

    def lab_to_rgb(self, L, a, b_lab):
        X, Y, Z = self.lab_to_xyz(L, a, b_lab)
        r, g, b, clipped = self.xyz_to_rgb(X, Y, Z)
        return r, g, b, clipped

    def rgb_to_xyz(self, r, g, b):
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0

        def gamma_correction(x):
            if x <= 0.04045:
                return x / 12.92
            else:
                return ((x + 0.055) / 1.055) ** 2.4

        r_linear = gamma_correction(r_norm)
        g_linear = gamma_correction(g_norm)
        b_linear = gamma_correction(b_norm)

        X = r_linear * 0.412453 + g_linear * 0.357580 + b_linear * 0.180423
        Y = r_linear * 0.212671 + g_linear * 0.715160 + b_linear * 0.072169
        Z = r_linear * 0.019334 + g_linear * 0.119193 + b_linear * 0.950227

        X *= 100
        Y *= 100
        Z *= 100

        return X, Y, Z

    def xyz_to_rgb(self, X, Y, Z):
        X /= 100
        Y /= 100
        Z /= 100

        r_linear = X * 3.2406 + Y * -1.5372 + Z * -0.4986
        g_linear = X * -0.9689 + Y * 1.8758 + Z * 0.0415
        b_linear = X * 0.0557 + Y * -0.2040 + Z * 1.0570

        def inverse_gamma(x):
            if x <= 0.0031308:
                return 12.92 * x
            else:
                return 1.055 * (x ** (1/2.4)) - 0.055

        r_norm = inverse_gamma(r_linear)
        g_norm = inverse_gamma(g_linear)
        b_norm = inverse_gamma(b_linear)

        clipped = False
        r = r_norm * 255
        g = g_norm * 255
        b = b_norm * 255

        if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255:
            clipped = True
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

        return int(round(r)), int(round(g)), int(round(b)), clipped

    def xyz_to_lab(self, X, Y, Z):
        X_w = 95.047
        Y_w = 100.0
        Z_w = 108.883

        x_norm = X / X_w
        y_norm = Y / Y_w
        z_norm = Z / Z_w

        def f(t):
            if t > 0.008856:
                return t ** (1/3)
            else:
                return 7.787 * t + 16/116

        fx = f(x_norm)
        fy = f(y_norm)
        fz = f(z_norm)

        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)

        return L, a, b

    def lab_to_xyz(self, L, a, b):
        X_w = 95.047
        Y_w = 100.0
        Z_w = 108.883

        fy = (L + 16) / 116
        fx = a / 500 + fy
        fz = fy - b / 200

        def f_inv(t):
            if t > 0.008856 ** (1/3):
                return t ** 3
            else:
                return (t - 16/116) / 7.787

        x_norm = f_inv(fx)
        y_norm = f_inv(fy)
        z_norm = f_inv(fz)

        X = x_norm * X_w
        Y = y_norm * Y_w
        Z = z_norm * Z_w

        return X, Y, Z

if __name__ == "__main__":
    root = ctk.CTk()
    app = ColorConverterApp(root)
    root.mainloop()