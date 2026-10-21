import tkinter as tk
from tkinter import ttk, messagebox


def fmt(num):
    """Formatea números quitando decimales innecesarios (.0)."""
    redondeado = round(float(num), 4)
    if abs(redondeado) < 1e-7:
        return "0"
    if abs(redondeado - round(redondeado)) < 1e-7:
        return str(int(round(redondeado)))
    return str(redondeado)


class AppEsquinaNoroeste:
    def __init__(self, root):
        self.root = root
        self.root.title("Método de la Esquina Noroeste - Investigación de Operaciones")
        self.root.geometry("1180x700")
        self.root.minsize(950, 600)
        self.root.configure(bg="#F1F5F9")

        # Dimensiones iniciales
        self.var_origenes = tk.IntVar(value=3)
        self.var_destinos = tk.IntVar(value=4)

        # Variables de la tabla editable
        self.vars_nombres_orig = []
        self.vars_nombres_dest = []
        self.vars_costos = []
        self.vars_ofertas = []
        self.vars_demandas = []

        # Datos de la solución y control de reproducción automática
        self.pasos = []
        self.datos_solucion = None
        self.indice_paso = 0
        self.reproduciendo = False
        self.timer_id = None

        self._construir_interfaz()
        self.cargar_ejemplo()

    # =========================================================================
    # 1. CONSTRUCCIÓN DE LA INTERFAZ GRÁFICA
    # =========================================================================
    def _construir_interfaz(self):
        # Barra superior
        header = tk.Frame(self.root, bg="#1E3A8A", pady=10, padx=15)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Método de la Esquina Noroeste",
            font=("Segoe UI", 14, "bold"),
            bg="#1E3A8A",
            fg="white",
        ).pack(side="left")

        # Contenedor principal dividido en Izquierda (Edición) y Derecha (Solución)
        panel_principal = ttk.PanedWindow(self.root, orient="horizontal")
        panel_principal.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_izq = tk.LabelFrame(
            panel_principal,
            text=" 1. Datos del Problema (Tabla Editable) ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#1E3A8A",
            padx=10,
            pady=10,
        )
        self.frame_der = tk.LabelFrame(
            panel_principal,
            text=" 2. Resolución Paso a Paso y Reproducción Automática ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#1E3A8A",
            padx=10,
            pady=10,
        )
        panel_principal.add(self.frame_izq, weight=1)
        panel_principal.add(self.frame_der, weight=1)

        self._armar_panel_izquierdo()
        self._armar_panel_derecho()

    def _armar_panel_izquierdo(self):
        # Controles de tamaño de la tabla
        barra_tam = tk.Frame(self.frame_izq, bg="white")
        barra_tam.pack(fill="x", pady=(0, 8))

        tk.Label(barra_tam, text="Orígenes:", bg="white", font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Spinbox(barra_tam, from_=1, to=15, textvariable=self.var_origenes, width=4).pack(side="left", padx=4)

        tk.Label(barra_tam, text="Destinos:", bg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 0))
        ttk.Spinbox(barra_tam, from_=1, to=15, textvariable=self.var_destinos, width=4).pack(side="left", padx=4)

        ttk.Button(barra_tam, text="Cambiar tamaño", command=self.redimensionar_tabla).pack(side="left", padx=6)
        ttk.Button(barra_tam, text="Cargar ejemplo", command=self.cargar_ejemplo).pack(side="left", padx=4)
        ttk.Button(barra_tam, text="Limpiar", command=self.limpiar_tabla).pack(side="left", padx=4)

        # Área desplazable para la tabla editable
        contenedor_scroll = tk.Frame(self.frame_izq, bg="white", bd=1, relief="solid")
        contenedor_scroll.pack(fill="both", expand=True, pady=4)

        self.canvas_izq = tk.Canvas(contenedor_scroll, bg="white", highlightthickness=0)
        scroll_y = ttk.Scrollbar(contenedor_scroll, orient="vertical", command=self.canvas_izq.yview)
        scroll_x = ttk.Scrollbar(contenedor_scroll, orient="horizontal", command=self.canvas_izq.xview)
        self.interior_tabla_izq = tk.Frame(self.canvas_izq, bg="white", padx=8, pady=8)

        self.canvas_izq.create_window((0, 0), window=self.interior_tabla_izq, anchor="nw")
        self.canvas_izq.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.canvas_izq.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor_scroll.grid_rowconfigure(0, weight=1)
        contenedor_scroll.grid_columnconfigure(0, weight=1)

        self.interior_tabla_izq.bind(
            "<Configure>",
            lambda e: self.canvas_izq.configure(scrollregion=self.canvas_izq.bbox("all")),
        )

        # Estado del balance en vivo y botón para resolver
        self.lbl_balance_vivo = tk.Label(
            self.frame_izq,
            text="Oferta: 0 | Demanda: 0",
            font=("Segoe UI", 9, "bold"),
            bg="#E2E8F0",
            pady=6,
        )
        self.lbl_balance_vivo.pack(fill="x", pady=6)

        btn_resolver = tk.Button(
            self.frame_izq,
            text="Resolver Problema",
            font=("Segoe UI", 10, "bold"),
            bg="#1D4ED8",
            fg="white",
            pady=6,
            cursor="hand2",
            command=self.resolver_problema,
        )
        btn_resolver.pack(fill="x")

    def _armar_panel_derecho(self):
        # Controles de paso a paso y reproducción automática
        barra_pasos = tk.Frame(self.frame_der, bg="white")
        barra_pasos.pack(fill="x", pady=(0, 8))

        ttk.Button(barra_pasos, text="◀ Paso anterior", command=self.paso_anterior).pack(side="left", padx=2)
        self.lbl_num_paso = tk.Label(
            barra_pasos,
            text="Paso 0 / 0",
            font=("Segoe UI", 10, "bold"),
            bg="#DBEAFE",
            fg="#1E3A8A",
            padx=12,
            pady=3,
        )
        self.lbl_num_paso.pack(side="left", padx=6)
        ttk.Button(barra_pasos, text="Siguiente paso ▶", command=self.paso_siguiente).pack(side="left", padx=2)

        self.btn_auto = tk.Button(
            barra_pasos,
            text="▶ Reproducción Automática",
            font=("Segoe UI", 9, "bold"),
            bg="#059669",
            fg="white",
            padx=10,
            cursor="hand2",
            command=self.alternar_reproduccion_auto,
        )
        self.btn_auto.pack(side="right", padx=4)

        # Área desplazable para mostrar la matriz de asignaciones paso a paso
        contenedor_sol = tk.Frame(self.frame_der, bg="white", bd=1, relief="solid")
        contenedor_sol.pack(fill="both", expand=True, pady=4)

        self.canvas_der = tk.Canvas(contenedor_sol, bg="white", highlightthickness=0)
        scroll_y2 = ttk.Scrollbar(contenedor_sol, orient="vertical", command=self.canvas_der.yview)
        scroll_x2 = ttk.Scrollbar(contenedor_sol, orient="horizontal", command=self.canvas_der.xview)
        self.interior_tabla_der = tk.Frame(self.canvas_der, bg="white", padx=8, pady=8)

        self.canvas_der.create_window((0, 0), window=self.interior_tabla_der, anchor="nw")
        self.canvas_der.configure(yscrollcommand=scroll_y2.set, xscrollcommand=scroll_x2.set)

        self.canvas_der.grid(row=0, column=0, sticky="nsew")
        scroll_y2.grid(row=0, column=1, sticky="ns")
        scroll_x2.grid(row=1, column=0, sticky="ew")
        contenedor_sol.grid_rowconfigure(0, weight=1)
        contenedor_sol.grid_columnconfigure(0, weight=1)

        self.interior_tabla_der.bind(
            "<Configure>",
            lambda e: self.canvas_der.configure(scrollregion=self.canvas_der.bbox("all")),
        )

        # Cuadro inferior con la explicación del paso y el Costo Total
        self.txt_salida = tk.Text(
            self.frame_der,
            height=11,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#F8FAFC",
            padx=8,
            pady=8,
            bd=1,
            relief="solid",
        )
        self.txt_salida.pack(fill="x", pady=(6, 0))
        self.txt_salida.configure(state="disabled")

    # =========================================================================
    # 2. GESTIÓN DE LA TABLA EDITABLE
    # =========================================================================
    def crear_tabla_editable(self, m, n, orig_prev=None, dest_prev=None, costos_prev=None, of_prev=None, dem_prev=None):
        self.detener_reproduccion()
        for w in self.interior_tabla_izq.winfo_children():
            w.destroy()

        self.var_origenes.set(m)
        self.var_destinos.set(n)
        self.vars_nombres_orig = []
        self.vars_nombres_dest = []
        self.vars_costos = []
        self.vars_ofertas = []
        self.vars_demandas = []

        # Esquina superior
        tk.Label(
            self.interior_tabla_izq,
            text="Origen \\ Destino",
            font=("Segoe UI", 9, "bold"),
            bg="#1E3A8A",
            fg="white",
            width=14,
            pady=5,
        ).grid(row=0, column=0, padx=1, pady=1)

        # Encabezados de destinos editables
        for j in range(n):
            nombre = dest_prev[j] if (dest_prev and j < len(dest_prev)) else f"D{j+1}"
            var_d = tk.StringVar(value=nombre)
            self.vars_nombres_dest.append(var_d)
            tk.Entry(
                self.interior_tabla_izq,
                textvariable=var_d,
                font=("Segoe UI", 9, "bold"),
                bg="#DBEAFE",
                justify="center",
                width=10,
                relief="solid",
                bd=1,
            ).grid(row=0, column=j + 1, padx=1, pady=1, ipady=3)

        tk.Label(
            self.interior_tabla_izq,
            text="Oferta",
            font=("Segoe UI", 9, "bold"),
            bg="#0F766E",
            fg="white",
            width=10,
            pady=5,
        ).grid(row=0, column=n + 1, padx=1, pady=1)

        # Filas de orígenes, costos y ofertas
        for i in range(m):
            nombre = orig_prev[i] if (orig_prev and i < len(orig_prev)) else f"O{i+1}"
            var_o = tk.StringVar(value=nombre)
            self.vars_nombres_orig.append(var_o)
            tk.Entry(
                self.interior_tabla_izq,
                textvariable=var_o,
                font=("Segoe UI", 9, "bold"),
                bg="#DBEAFE",
                justify="center",
                width=14,
                relief="solid",
                bd=1,
            ).grid(row=i + 1, column=0, padx=1, pady=1, ipady=3)

            fila_c = []
            for j in range(n):
                val = (
                    costos_prev[i][j]
                    if (costos_prev and i < len(costos_prev) and j < len(costos_prev[i]))
                    else "0"
                )
                var_c = tk.StringVar(value=val)
                fila_c.append(var_c)
                tk.Entry(
                    self.interior_tabla_izq,
                    textvariable=var_c,
                    font=("Segoe UI", 10),
                    justify="center",
                    width=10,
                    relief="solid",
                    bd=1,
                ).grid(row=i + 1, column=j + 1, padx=1, pady=1, ipady=3)
            self.vars_costos.append(fila_c)

            val_of = of_prev[i] if (of_prev and i < len(of_prev)) else "0"
            var_of = tk.StringVar(value=val_of)
            var_of.trace_add("write", lambda *_: self.actualizar_balance_vivo())
            self.vars_ofertas.append(var_of)
            tk.Entry(
                self.interior_tabla_izq,
                textvariable=var_of,
                font=("Segoe UI", 10, "bold"),
                bg="#ECFDF5",
                justify="center",
                width=10,
                relief="solid",
                bd=1,
            ).grid(row=i + 1, column=n + 1, padx=1, pady=1, ipady=3)

        # Fila inferior de demandas
        tk.Label(
            self.interior_tabla_izq,
            text="Demanda",
            font=("Segoe UI", 9, "bold"),
            bg="#0F766E",
            fg="white",
            width=14,
            pady=5,
        ).grid(row=m + 1, column=0, padx=1, pady=1)

        for j in range(n):
            val_dem = dem_prev[j] if (dem_prev and j < len(dem_prev)) else "0"
            var_dem = tk.StringVar(value=val_dem)
            var_dem.trace_add("write", lambda *_: self.actualizar_balance_vivo())
            self.vars_demandas.append(var_dem)
            tk.Entry(
                self.interior_tabla_izq,
                textvariable=var_dem,
                font=("Segoe UI", 10, "bold"),
                bg="#ECFDF5",
                justify="center",
                width=10,
                relief="solid",
                bd=1,
            ).grid(row=m + 1, column=j + 1, padx=1, pady=1, ipady=3)

        self.actualizar_balance_vivo()

    def redimensionar_tabla(self):
        try:
            m = max(1, int(self.var_origenes.get()))
            n = max(1, int(self.var_destinos.get()))
        except ValueError:
            messagebox.showerror("Error", "Introduce cantidades enteras válidas para orígenes y destinos.")
            return

        orig = [v.get() for v in self.vars_nombres_orig]
        dest = [v.get() for v in self.vars_nombres_dest]
        costos = [[v.get() for v in fila] for fila in self.vars_costos]
        of = [v.get() for v in self.vars_ofertas]
        dem = [v.get() for v in self.vars_demandas]
        self.crear_tabla_editable(m, n, orig, dest, costos, of, dem)

    def limpiar_tabla(self):
        if messagebox.askyesno("Limpiar", "¿Deseas poner en cero todos los datos de la tabla?"):
            self.crear_tabla_editable(self.var_origenes.get(), self.var_destinos.get())

    def cargar_ejemplo(self):
        orig = ["O1", "O2", "O3"]
        dest = ["D1", "D2", "D3", "D4"]
        costos = [
            ["10", "2", "20", "11"],
            ["12", "7", "9", "20"],
            ["4", "14", "16", "18"],
        ]
        ofertas = ["15", "25", "10"]
        demandas = ["5", "15", "15", "15"]
        self.crear_tabla_editable(3, 4, orig, dest, costos, ofertas, demandas)
        self.resolver_problema()

    def actualizar_balance_vivo(self):
        try:
            s_of = sum(float(v.get().replace(",", ".")) for v in self.vars_ofertas)
            s_dem = sum(float(v.get().replace(",", ".")) for v in self.vars_demandas)
        except ValueError:
            self.lbl_balance_vivo.configure(
                text="⚠ Revisa que todas las ofertas y demandas sean números válidos",
                bg="#FEE2E2",
                fg="#991B1B",
            )
            return

        dif = abs(s_of - s_dem)
        if dif < 1e-7:
            self.lbl_balance_vivo.configure(
                text=f"Oferta Total: {fmt(s_of)}  |  Demanda Total: {fmt(s_dem)}  →  PROBLEMA BALANCEADO",
                bg="#D1FAE5",
                fg="#065F46",
            )
        else:
            tipo = "Destino Ficticio" if s_of > s_dem else "Origen Ficticio"
            self.lbl_balance_vivo.configure(
                text=f"Oferta: {fmt(s_of)} | Demanda: {fmt(s_dem)} (Diferencia: {fmt(dif)}) → Se agregará {tipo}",
                bg="#FEF3C7",
                fg="#92400E",
            )

    # =========================================================================
    # 3. ALGORITMO DE ESQUINA NOROESTE Y BALANCEO AUTOMÁTICO
    # =========================================================================
    def resolver_problema(self):
        self.detener_reproduccion()

        # 1. Leer y validar datos de la tabla
        try:
            orig = [v.get().strip() or f"O{i+1}" for i, v in enumerate(self.vars_nombres_orig)]
            dest = [v.get().strip() or f"D{j+1}" for j, v in enumerate(self.vars_nombres_dest)]
            costos = [[float(c.get().replace(",", ".")) for c in fila] for fila in self.vars_costos]
            ofertas = [float(o.get().replace(",", ".")) for o in self.vars_ofertas]
            demandas = [float(d.get().replace(",", ".")) for d in self.vars_demandas]
        except ValueError:
            messagebox.showerror(
                "Datos inválidos",
                "Verifica que no existan celdas vacías ni letras en los costos, ofertas o demandas.",
            )
            return

        if any(x < 0 for x in ofertas) or any(x < 0 for x in demandas):
            messagebox.showerror("Error", "Las ofertas y demandas no pueden ser negativas.")
            return

        if sum(ofertas) <= 0 and sum(demandas) <= 0:
            messagebox.showerror("Error", "La suma de ofertas y demandas debe ser mayor que cero.")
            return

        # 2. Balanceo automático si oferta != demanda
        s_of = sum(ofertas)
        s_dem = sum(demandas)
        dif = round(abs(s_of - s_dem), 6)
        nota_balanceo = "El problema original ya estaba balanceado."

        if dif > 1e-7:
            if s_of > s_dem:
                dest.append("D. Ficticio")
                for fila in costos:
                    fila.append(0.0)
                demandas.append(dif)
                nota_balanceo = f"No balanceado (Oferta > Demanda): Se agregó un Destino Ficticio con demanda {fmt(dif)} y costo 0."
            else:
                orig.append("O. Ficticio")
                costos.append([0.0] * len(dest))
                ofertas.append(dif)
                nota_balanceo = f"No balanceado (Demanda > Oferta): Se agregó un Origen Ficticio con oferta {fmt(dif)} y costo 0."

        # 3. Ejecutar el método de la Esquina Noroeste guardando cada paso
        m, n = len(orig), len(dest)
        of_rest = list(ofertas)
        dem_rest = list(demandas)
        asignaciones = [[None for _ in range(n)] for _ in range(m)]
        self.pasos = []

        i, j = 0, 0
        num_paso = 1

        while i < m and j < n:
            of_disp = of_rest[i]
            dem_pend = dem_rest[j]
            asig = min(of_disp, dem_pend)

            asignaciones[i][j] = asig
            of_rest[i] = round(of_disp - asig, 6)
            dem_rest[j] = round(dem_pend - asig, 6)

            if abs(of_rest[i]) < 1e-7 and abs(dem_rest[j]) < 1e-7:
                if i == m - 1 and j == n - 1:
                    motivo = "Se satisfacen simultáneamente la última oferta y demanda. Fin del método."
                else:
                    motivo = f"Se agotan al mismo tiempo la oferta de {orig[i]} y la demanda de {dest[j]}."
                sig_i, sig_j = i + 1, j if (i + 1 < m) else (i, j + 1)
            elif abs(of_rest[i]) < 1e-7:
                motivo = f"Se agota la oferta de {orig[i]} (queda 0), avanzamos a la siguiente fila."
                sig_i, sig_j = i + 1, j
            else:
                motivo = f"Se cubre la demanda de {dest[j]} (queda 0), avanzamos a la siguiente columna."
                sig_i, sig_j = i, j + 1

            explicacion = (
                f"Paso {num_paso}: Celda [{orig[i]} → {dest[j]}] | "
                f"Oferta disp.: {fmt(of_disp)}, Demanda pend.: {fmt(dem_pend)} → "
                f"Asignamos {fmt(asig)} unidades.\n"
                f"Queda Oferta = {fmt(of_rest[i])} y Demanda = {fmt(dem_rest[j])}. {motivo}"
            )

            self.pasos.append({
                "num": num_paso,
                "fila": i,
                "col": j,
                "matriz": [list(f) for f in asignaciones],
                "of_rest": list(of_rest),
                "dem_rest": list(dem_rest),
                "explicacion": explicacion,
            })

            i, j = sig_i, sig_j
            num_paso += 1

        # 4. Calcular el desglose del Costo Total
        partes_mult = []
        partes_suma = []
        costo_total = 0.0

        for r in range(m):
            for c in range(n):
                val = asignaciones[r][c]
                if val is not None and val > 1e-7:
                    cu = costos[r][c]
                    sub = val * cu
                    costo_total += sub
                    partes_mult.append(f"({fmt(val)} × {fmt(cu)})")
                    partes_suma.append(fmt(sub))

        self.datos_solucion = {
            "orig": orig,
            "dest": dest,
            "costos": costos,
            "ofertas": ofertas,
            "demandas": demandas,
            "nota_balanceo": nota_balanceo,
            "str_mult": " + ".join(partes_mult) if partes_mult else "0",
            "str_suma": " + ".join(partes_suma) if partes_suma else "0",
            "costo_total": fmt(costo_total),
        }

        self.indice_paso = 0
        self.mostrar_paso_actual()

    # =========================================================================
    # 4. VISUALIZACIÓN PASO A PASO Y REPRODUCCIÓN AUTOMÁTICA
    # =========================================================================
    def mostrar_paso_actual(self):
        if not self.pasos or not self.datos_solucion:
            return

        paso = self.pasos[self.indice_paso]
        sol = self.datos_solucion
        m, n = len(sol["orig"]), len(sol["dest"])

        self.lbl_num_paso.configure(text=f"Paso {paso['num']} / {len(self.pasos)}")

        # Redibujar tabla de solución
        for w in self.interior_tabla_der.winfo_children():
            w.destroy()

        tk.Label(
            self.interior_tabla_der,
            text="Origen \\ Destino",
            font=("Segoe UI", 9, "bold"),
            bg="#1E3A8A",
            fg="white",
            width=13,
            pady=5,
        ).grid(row=0, column=0, padx=1, pady=1)

        for j in range(n):
            tk.Label(
                self.interior_tabla_der,
                text=sol["dest"][j],
                font=("Segoe UI", 9, "bold"),
                bg="#DBEAFE",
                fg="#1E3A8A",
                width=13,
                pady=5,
                relief="solid",
                bd=1,
            ).grid(row=0, column=j + 1, padx=1, pady=1)

        tk.Label(
            self.interior_tabla_der,
            text="Oferta (Rest.)",
            font=("Segoe UI", 9, "bold"),
            bg="#0F766E",
            fg="white",
            width=13,
            pady=5,
        ).grid(row=0, column=n + 1, padx=1, pady=1)

        for i in range(m):
            tk.Label(
                self.interior_tabla_der,
                text=sol["orig"][i],
                font=("Segoe UI", 9, "bold"),
                bg="#DBEAFE",
                fg="#1E3A8A",
                width=13,
                pady=8,
                relief="solid",
                bd=1,
            ).grid(row=i + 1, column=0, padx=1, pady=1)

            for j in range(n):
                val = paso["matriz"][i][j]
                costo = fmt(sol["costos"][i][j])

                if i == paso["fila"] and j == paso["col"]:
                    bg_color = "#93C5FD"  # Azul: Celda activa en este paso
                elif val is not None:
                    bg_color = "#A7F3D0"  # Verde: Celda ya asignada
                else:
                    bg_color = "white"

                texto_celda = f"Asig: {fmt(val)}\n[Costo: {costo}]" if val is not None else f"—\n[Costo: {costo}]"
                tk.Label(
                    self.interior_tabla_der,
                    text=texto_celda,
                    font=("Segoe UI", 9, "bold" if val is not None else "normal"),
                    bg=bg_color,
                    width=13,
                    pady=6,
                    relief="solid",
                    bd=1,
                ).grid(row=i + 1, column=j + 1, padx=1, pady=1)

            of_ini = fmt(sol["ofertas"][i])
            of_res = fmt(paso["of_rest"][i])
            tk.Label(
                self.interior_tabla_der,
                text=f"{of_ini} → {of_res}",
                font=("Segoe UI", 9, "bold"),
                bg="#ECFDF5",
                fg="#065F46",
                width=13,
                pady=8,
                relief="solid",
                bd=1,
            ).grid(row=i + 1, column=n + 1, padx=1, pady=1)

        tk.Label(
            self.interior_tabla_der,
            text="Demanda (Rest.)",
            font=("Segoe UI", 9, "bold"),
            bg="#0F766E",
            fg="white",
            width=13,
            pady=5,
        ).grid(row=m + 1, column=0, padx=1, pady=1)

        for j in range(n):
            dem_ini = fmt(sol["demandas"][j])
            dem_res = fmt(paso["dem_rest"][j])
            tk.Label(
                self.interior_tabla_der,
                text=f"{dem_ini} → {dem_res}",
                font=("Segoe UI", 9, "bold"),
                bg="#ECFDF5",
                fg="#065F46",
                width=13,
                pady=5,
                relief="solid",
                bd=1,
            ).grid(row=m + 1, column=j + 1, padx=1, pady=1)

        # Actualizar cuadro de texto con la explicación y el costo total
        resumen = (
            f"• {sol['nota_balanceo']}\n"
            f"--------------------------------------------------------------------------------\n"
            f"{paso['explicacion']}\n"
            f"--------------------------------------------------------------------------------\n"
            f"CÁLCULO DEL COSTO TOTAL (Solución Básica Factible Inicial):\n"
            f"  Costo Total = {sol['str_mult']}\n"
            f"  Costo Total = {sol['str_suma']} = {sol['costo_total']}"
        )
        self.txt_salida.configure(state="normal")
        self.txt_salida.delete("1.0", tk.END)
        self.txt_salida.insert(tk.END, resumen)
        self.txt_salida.configure(state="disabled")

    def paso_anterior(self):
        self.detener_reproduccion()
        if self.indice_paso > 0:
            self.indice_paso -= 1
            self.mostrar_paso_actual()

    def paso_siguiente(self):
        self.detener_reproduccion()
        if self.indice_paso < len(self.pasos) - 1:
            self.indice_paso += 1
            self.mostrar_paso_actual()

    def alternar_reproduccion_auto(self):
        if not self.pasos:
            return
        if self.reproduciendo:
            self.detener_reproduccion()
        else:
            if self.indice_paso >= len(self.pasos) - 1:
                self.indice_paso = 0
            self.reproduciendo = True
            self.btn_auto.configure(text="⏸ Pausar Reproducción", bg="#D97706")
            self._ciclo_auto()

    def _ciclo_auto(self):
        if not self.reproduciendo:
            return
        self.mostrar_paso_actual()
        if self.indice_paso < len(self.pasos) - 1:
            self.indice_paso += 1
            self.timer_id = self.root.after(1100, self._ciclo_auto)
        else:
            self.detener_reproduccion()

    def detener_reproduccion(self):
        self.reproduciendo = False
        if self.timer_id is not None:
            try:
                self.root.after_cancel(self.timer_id)
            except ValueError:
                pass
            self.timer_id = None
        if hasattr(self, "btn_auto"):
            self.btn_auto.configure(text="▶ Reproducción Automática", bg="#059669")


if __name__ == "__main__":
    ventana = tk.Tk()
    app = AppEsquinaNoroeste(ventana)
    ventana.mainloop()