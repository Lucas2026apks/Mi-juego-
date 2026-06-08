import pygame
import random
import json
import os
import math
from sys import exit

# --- CONFIGURACIÓN BASE ---
pygame.init()
ANCHO, ALTO = 1000, 700
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("GUERRERO 63KM: CHULUPI EDITION (LostMiner Style)")
reloj = pygame.time.Clock()

# --- VARIABLES DE CONTROL TÁCTIL ---
control_tactil = True  
ultimo_guardado = pygame.time.get_ticks()

# Configuración de botones en fila inferior para evitar conflictos
ANCHO_B, ALTO_B = 80, 70
Y_BOTONES = ALTO - 90
rect_btn_izq = pygame.Rect(30, Y_BOTONES, ANCHO_B, ALTO_B)
rect_btn_der = pygame.Rect(130, Y_BOTONES, ANCHO_B, ALTO_B)
rect_btn_salto = pygame.Rect(230, Y_BOTONES, ANCHO_B, ALTO_B)

rect_btn_a = pygame.Rect(ANCHO - 120, Y_BOTONES, 90, ALTO_B)
rect_btn_t = pygame.Rect(ANCHO - 100, 20, 80, 80)
rect_btn_inv = pygame.Rect(20, 100, 70, 70) 

# --- CARGADOR DE IMÁGENES ---
def cargar_img(archivo, escala):
    ruta = f"{archivo}.png"
    if os.path.exists(ruta):
        try:
            img = pygame.image.load(ruta).convert_alpha()
            return pygame.transform.scale(img, escala)
        except: return None
    return None

IMG = {
    "arbol": cargar_img("arbol", (90, 110)), 
    "roca": cargar_img("roca", (65, 55)),
    "ogro": cargar_img("ogro", (60, 60)),
    "flechero": cargar_img("flechero", (60, 60)),
    "ladron": cargar_img("ladron", (55, 55)), 
    "chulupi": cargar_img("chulupi", (50, 50)),
    "jefe": cargar_img("jefefinal", (280, 320)),
    "hombre": cargar_img("personaje_hombre", (55, 75)), 
    "mujer": cargar_img("personaje_mujer", (55, 75)),
    "flecha": cargar_img("flecha", (35, 12)), 
    "cofre": cargar_img("cofre_del_tesoro", (45, 45)),
    "pez": cargar_img("pez", (40, 40)), 
    "piraña": cargar_img("piraña", (40, 40)),
    "lago": cargar_img("lago", (400, 180)),
    "Caña de Pescar": cargar_img("caña_de_pescar", (50, 50)),
    "vendedor": cargar_img("Vendedor", (80, 100)),
    "Arco": cargar_img("arco", (55, 55))
}

# --- DICCIONARIO MAESTRO ---
MATERIALES = ["madera", "piedra", "cobre", "hierro", "oro", "diamante"]
PRECIOS = [100, 400, 800, 1500, 3000, 6000]
DAÑOS = [60, 120, 250, 450, 700, 1200]
PROT = [0.10, 0.25, 0.40, 0.55, 0.70, 0.90]

INFO_ITEMS = {
    "Pez": {"heal": 20, "tipo": "comida", "ico": "🐟"},
    "Piraña": {"heal": -15, "tipo": "comida", "ico": "💀"},
    "Poción Vida": {"heal": 80, "tipo": "pocion", "precio": 250, "ico": "🧪"},
    "Caña de Pescar": {"tipo": "caña", "precio": 300, "ico": "🎣"},
    "Flecha": {"tipo": "ammo", "precio": 20, "ico": "➹"},
    "Arco": {"dmg": 150, "tipo": "arco", "precio": 1200, "ico": "🏹"},
    None: {"tipo": "none", "ico": ""}
}

MEJORAS = {"Espada": [], "Pico": [], "Peto": []}
for i, mat in enumerate(MATERIALES):
    n_espada = f"Espada {mat.capitalize()}"; n_pico = f"Pico {mat.capitalize()}"; n_peto = f"Peto {mat.capitalize()}"
    IMG[n_espada] = cargar_img(f"espada_de_{mat}", (50, 50))
    IMG[n_pico] = cargar_img("pico_hierro" if mat=="hierro" else f"pico_de_{mat}", (50, 50))
    IMG[n_peto] = cargar_img(f"Peto {mat.capitalize()}", (50, 50))
    INFO_ITEMS[n_espada] = {"dmg": DAÑOS[i], "tipo": "arma", "precio": PRECIOS[i], "ico": "⚔"}
    INFO_ITEMS[n_pico] = {"dmg": DAÑOS[i]//2, "tipo": "pico", "precio": PRECIOS[i]-50, "ico": "⛏"}
    INFO_ITEMS[n_peto] = {"prot": PROT[i], "tipo": "armadura", "precio": PRECIOS[i]+300, "ico": "👕"}
    MEJORAS["Espada"].append(n_espada); MEJORAS["Pico"].append(n_pico); MEJORAS["Peto"].append(n_peto)

# --- VARIABLES DE ESTADO ---
estado = "MENU_PRINCIPAL"
slot_actual, modo_actual, genero_actual = 1, "SUPERVIVENCIA", "hombre"
oro, dist_rec, hp, slot_sel = 1000, 0, 100, 0
hb = [None]*9; mochila = []; proyectiles = []
aviso_txt = {"t": "", "frames": 0}; item_arrastrado = None 
tiempo_inicio_sesion = 0; tiempo_previo_total = 0

# --- ENTORNO Y FÍSICAS (LOSTMINER STYLE) ---
TAMANIO_BLOQUE = 50
ALTURA_SUELO = 450  # El bloque superior de pasto empieza en Y = 450

COLORES_BLOQUES = {
    1: (40, 180, 99),   # Verde Pasto
    2: (120, 120, 120)  # Gris Piedra
}

# Jugador dimensiones fijas
pj_ancho, pj_alto = 55, 75
pj_real_x = 200
pj_real_y = ALTURA_SUELO - pj_alto

vel_x = 0
vel_y = 0
GRAVEDAD = 0.6
EN_SUELO = False

# --- FUNCIONES AUXILIARES ---
def lanzar_aviso(msg): global aviso_txt; aviso_txt = {"t": msg, "frames": 90}
def obtener_ruta(n): return f"mundo_{n}.json"
def obtener_tiempo_actual():
    if estado in ["MENU_PRINCIPAL", "SELECCION_SLOT", "CONFIG_MUNDO", "AJUSTES", "CONTROLES"]: return tiempo_previo_total
    return tiempo_previo_total + (pygame.time.get_ticks() - tiempo_inicio_sesion)

def obtener_siguiente_mejora(tipo):
    lista = MEJORAS[tipo]; posesiones = [it for it in (hb + mochila) if it is not None]
    indice_max = -1
    for i, nombre in enumerate(lista):
        if nombre in posesiones: indice_max = i
    return lista[indice_max + 1] if indice_max + 1 < len(lista) else None

def guardar_mundo():
    try:
        datos = {"oro": oro, "dist": dist_rec, "hp": hp, "hb": hb, "mochila": mochila, 
                 "modo": modo_actual, "genero": genero_actual, "tiempo": obtener_tiempo_actual()}
        with open(obtener_ruta(slot_actual), "w") as f: json.dump(datos, f)
        lanzar_aviso("PROGRESO GUARDADO")
    except: pass

def cargar_mundo(n):
    global oro, dist_rec, hp, hb, mochila, modo_actual, genero_actual, slot_actual, tiempo_previo_total, tiempo_inicio_sesion, pj_real_x, pj_real_y
    slot_actual = n
    if os.path.exists(obtener_ruta(n)):
        with open(obtener_ruta(n), "r") as f:
            d = json.load(f); oro, dist_rec, hp, hb, mochila = d["oro"], d["dist"], d["hp"], d["hb"], d["mochila"]
            modo_actual, genero_actual = d.get("modo", "SUPERVIVENCIA"), d.get("genero", "hombre")
            tiempo_previo_total = d.get("tiempo", 0); tiempo_inicio_sesion = pygame.time.get_ticks()
            pj_real_x = 200
            pj_real_y = ALTURA_SUELO - pj_alto
            return True
    return False

def reset_stats():
    global oro, dist_rec, hp, hb, mochila, proyectiles, tiempo_inicio_sesion, tiempo_previo_total, pj_real_x, pj_real_y
    oro, dist_rec, hp, proyectiles = 1000, 0, 100, []
    hb = ["Espada Madera", "Pico Madera", "Caña de Pescar", "Arco"] + [None]*5
    mochila = ["Flecha"] * 10
    pj_real_x = 200
    pj_real_y = ALTURA_SUELO - pj_alto
    tiempo_previo_total = 0; tiempo_inicio_sesion = pygame.time.get_ticks()

# --- INTERFAZ ---
f_tit = pygame.font.SysFont("serif", 60, True); f_gui = pygame.font.SysFont("monospace", 18, True); f_sm = pygame.font.SysFont("monospace", 14, True)

def boton(txt, x, y, w, h, col):
    rect = pygame.Rect(x, y, w, h); m_pos = pygame.mouse.get_pos(); clic = pygame.mouse.get_pressed()[0]
    final_col = (min(col[0]+30, 255), min(col[1]+30, 255), min(col[2]+30, 255)) if rect.collidepoint(m_pos) else col
    pygame.draw.rect(pantalla, final_col, rect, border_radius=12)
    t_surf = f_gui.render(txt, True, (255,255,255))
    pantalla.blit(t_surf, t_surf.get_rect(center=rect.center))
    return rect.collidepoint(m_pos) and clic

def dibujar_item(nombre, rect):
    if nombre is None: return
    img = IMG.get(nombre)
    if img: pantalla.blit(pygame.transform.scale(img, (rect.width-10, rect.height-10)), (rect.x+5, rect.y+5))
    else:
        inf = INFO_ITEMS.get(nombre, INFO_ITEMS[None]); txt = f_sm.render(inf.get("ico", "?"), True, (255,255,255))
        pantalla.blit(txt, txt.get_rect(center=rect.center))

# --- GENERACIÓN DEL MUNDO AJUSTADA (Alturas perfectas en el suelo) ---
entorno = [{"t": random.choice(["arbol", "roca"]), "x": random.randint(600, 63000)} for _ in range(200)]
# Ajuste fino de la altura en base a la escala real del objeto
for obj in entorno:
    if obj["t"] == "arbol": obj["y"] = ALTURA_SUELO - 110
    else: obj["y"] = ALTURA_SUELO - 55

enemigos = [{"x": random.randint(1500, 62500), "y": ALTURA_SUELO - 60, "hp": 150, "v": True, 
             "t": random.choice(["ogro", "flechero", "ladron", "chulupi"])} for _ in range(250)]
bases = [{"x": i * 5000, "y": ALTURA_SUELO - 100} for i in range(1, 13)]
lagos = [{"x": i * 4000, "y": ALTURA_SUELO} for i in range(1, 17)]

# --- BUCLE PRINCIPAL ---
while True:
    ahora = pygame.time.get_ticks()
    m_pos = pygame.mouse.get_pos(); clic = pygame.mouse.get_pressed()
    
    if estado == "JUEGO" and ahora - ultimo_guardado > 120000:
        guardar_mundo(); ultimo_guardado = ahora

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT: pygame.quit(); exit()
        
        # --- TECLADO ---
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                if estado == "JUEGO": tiempo_previo_total = obtener_tiempo_actual(); estado = "PAUSA"
                elif estado == "PAUSA": tiempo_inicio_sesion = pygame.time.get_ticks(); estado = "JUEGO"
            if estado == "JUEGO":
                if ev.key == pygame.K_i: estado = "MOCHILA"
                if ev.key == pygame.K_g: guardar_mundo()

        # --- SELECCIÓN DIRECTA HOTBAR ---
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if estado == "JUEGO":
                for i in range(9):
                    r_hotbar = pygame.Rect(230 + i*65, ALTO-170, 60, 60)
                    if r_hotbar.collidepoint(m_pos): slot_sel = i; break
                
                # Botones Auxiliares Móvil
                if control_tactil and rect_btn_inv.collidepoint(m_pos): estado = "MOCHILA"
                if control_tactil and rect_btn_t.collidepoint(m_pos):
                    for b in bases:
                        if abs((b["x"] - dist_rec + 200) - pj_real_x) < 120: estado = "TIENDA"; break

        # --- DRAG AND DROP MOCHILA ---
        if estado == "MOCHILA" and ev.type == pygame.MOUSEBUTTONDOWN:
            for i, it in enumerate(mochila[:24]):
                if pygame.Rect(100+(i%6)*140, 150+(i//6)*120, 110, 100).collidepoint(m_pos): 
                    item_arrastrado = {"tipo": "mochila", "idx": i, "item": it}; break
            if not item_arrastrado:
                for i in range(9):
                    if pygame.Rect(230 + i*65, ALTO-85, 60, 60).collidepoint(m_pos) and hb[i]: 
                        item_arrastrado = {"tipo": "hb", "idx": i, "item": hb[i]}; break

        if estado == "MOCHILA" and ev.type == pygame.MOUSEBUTTONUP and item_arrastrado:
            destino = None
            for i in range(24):
                if pygame.Rect(100+(i%6)*140, 150+(i//6)*120, 110, 100).collidepoint(m_pos): destino = {"tipo": "mochila", "idx": i}; break
            if not destino:
                for i in range(9):
                    if pygame.Rect(230 + i*65, ALTO-85, 60, 60).collidepoint(m_pos): destino = {"tipo": "hb", "idx": i}; break
            
            if destino:
                orig_t, orig_idx, item = item_arrastrado["tipo"], item_arrastrado["idx"], item_arrastrado["item"]
                if orig_t == "mochila" and destino["tipo"] == "hb":
                    temp = hb[destino["idx"]]; hb[destino["idx"]] = item
                    if temp: mochila[orig_idx] = temp
                    else: mochila.pop(orig_idx)
                elif orig_t == "hb" and destino["tipo"] == "mochila":
                    if destino["idx"] < len(mochila): mochila[destino["idx"]], hb[orig_idx] = item, mochila[destino["idx"]]
                    else: mochila.append(item); hb[orig_idx] = None
                elif orig_t == "hb" and destino["tipo"] == "hb": hb[orig_idx], hb[destino["idx"]] = hb[destino["idx"]], hb[orig_idx]
            item_arrastrado = None

    # --- RENDERIZADO DE INTERFACES ---
    if estado == "MENU_PRINCIPAL":
        pantalla.fill((20, 20, 30))
        pantarma_tit = f_tit.render("GUERRERO 63KM", True, (255,215,0))
        pantalla.blit(pantarma_tit, (ANCHO//2 - pantarma_tit.get_width()//2, 150))
        if boton("JUGAR", 400, 300, 200, 60, (50, 120, 50)): estado = "SELECCION_SLOT"; pygame.time.delay(200)
        if boton("AJUSTES", 400, 400, 200, 60, (100, 100, 100)): estado = "AJUSTES"; pygame.time.delay(200)
        if boton("SALIR", 400, 500, 200, 60, (150, 50, 50)): pygame.quit(); exit()
    
    elif estado == "AJUSTES":
        pantalla.fill((20, 20, 30))
        pantalla.blit(f_tit.render("AJUSTES", True, (255, 255, 255)), (380, 150))
        if boton("CONTROLES: " + ("TACTIL" if control_tactil else "TECLADO"), 350, 300, 300, 60, (70, 70, 70)): 
            control_tactil = not control_tactil; pygame.time.delay(200)
        if boton("VOLVER", 400, 450, 200, 60, (150, 50, 50)): estado = "MENU_PRINCIPAL"

    elif estado == "SELECCION_SLOT":
        pantalla.fill((20, 20, 30))
        for i in range(1, 4):
            if boton(f"Slot {i} - {'CARGAR' if os.path.exists(obtener_ruta(i)) else 'NUEVO'}", 350, 150 + i*80, 300, 60, (70, 70, 100)):
                if cargar_mundo(i): estado = "JUEGO"
                else: slot_actual = i; reset_stats(); estado = "JUEGO"
                pygame.time.delay(200)

    elif estado == "PAUSA":
        pantalla.fill((30, 30, 40))
        txt_pausa = f_tit.render("PAUSA", True, (255, 255, 255))
        pantalla.blit(txt_pausa, (ANCHO//2 - txt_pausa.get_width()//2, 150))
        if boton("REANUDAR", 400, 280, 200, 60, (50, 120, 50)): tiempo_inicio_sesion = pygame.time.get_ticks(); estado = "JUEGO"
        if boton("GUARDAR", 400, 380, 200, 60, (100, 100, 100)): guardar_mundo()
        if boton("MENU PRINCIPAL", 400, 480, 200, 60, (150, 50, 50)): estado = "MENU_PRINCIPAL"

    elif estado == "JUEGO":
        # --- LÓGICA DE MOVIMIENTO DE JUGADOR (FÍSICAS 2D) ---
        vel_x = 0
        ejecutar_ataque = False

        if control_tactil:
            if clic[0]:
                if rect_btn_izq.collidepoint(m_pos): vel_x = -6
                if rect_btn_der.collidepoint(m_pos): vel_x = 6
                if rect_btn_salto.collidepoint(m_pos) and EN_SUELO:
                    vel_y = -13
                    EN_SUELO = False
                if rect_btn_a.collidepoint(m_pos):
                    ejecutar_ataque = True
        else:
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_a] or teclas[pygame.K_LEFT]: vel_x = -6
            if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]: vel_x = 6
            if (teclas[pygame.K_SPACE] or teclas[pygame.K_w]) and EN_SUELO:
                vel_y = -13
                EN_SUELO = False
            if clic[0] and m_pos[1] < ALTO - 180:
                ejecutar_ataque = True

        vel_y += GRAVEDAD
        if vel_y > 14: vel_y = 14

        dist_rec += vel_x
        if dist_rec < 0: dist_rec = 0
        
        pj_real_y += vel_y

        # Colisión con el suelo
        if pj_real_y >= ALTURA_SUELO - pj_alto:
            pj_real_y = ALTURA_SUELO - pj_alto
            vel_y = 0
            EN_SUELO = True

        # --- COMBATE ---
        if ejecutar_ataque:
            item = hb[slot_sel]; inf_item = INFO_ITEMS.get(item, {}); accion_hecha = False
            
            if item == "Arco":
                if "Flecha" in mochila:
                    proyectiles.append([pj_real_x + 30, pj_real_y + 30, 15]) 
                    mochila.remove("Flecha")
                    accion_hecha = True
                    pygame.time.delay(150)
                else: lanzar_aviso("¡SIN FLECHAS!")
            
            elif item and "heal" in inf_item: 
                hp = max(0, min(100, hp + inf_item["heal"]))
                hb[slot_sel] = None
                accion_hecha = True
                pygame.time.delay(150)
            
            elif item == "Caña de Pescar":
                if any(abs((l["x"] - dist_rec + pj_real_x) - pj_real_x) < 150 for l in lagos):
                    if len(mochila) < 24: 
                        mochila.append("Pez" if random.random() < 0.70 else "Piraña")
                        accion_hecha = True
                        pygame.time.delay(200)
                    else: lanzar_aviso("MOCHILA LLENA")
            
            if not accion_hecha: 
                for e in enemigos:
                    if e["v"] and abs((e["x"] - dist_rec + pj_real_x) - pj_real_x) < 90:
                        e["hp"] -= inf_item.get("dmg", 15) if item else 15
                        if e["hp"] <= 0: e["v"] = False; oro += 100
                        lanzar_aviso("¡GOLPE!")
                        pygame.time.delay(150)
                        break

        for proj in proyectiles[:]:
            proj[0] += proj[2] 
            if proj[0] > ANCHO: proyectiles.remove(proj); continue
            for e in enemigos:
                if e["v"] and abs((e["x"] - dist_rec + pj_real_x) - proj[0]) < 40:
                    e["hp"] -= 150 
                    if e["hp"] <= 0: e["v"] = False; oro += 100
                    if proj in proyectiles: proyectiles.remove(proj)
                    break

        # --- DIBUJAR JUEGO ---
        pantalla.fill((135, 206, 235)) 

        # 1. GENERACIÓN INFINITA DEL SUELO (Cálculo dinámico basado en dist_rec)
        offset_bloques = int(dist_rec % TAMANIO_BLOQUE)
        bloque_inicial = int(dist_rec // TAMANIO_BLOQUE)
        columnas_pantalla = (ANCHO // TAMANIO_BLOQUE) + 2

        for c in range(columnas_pantalla):
            bx = c * TAMANIO_BLOQUE - offset_bloques
            
            # Dibujar Fila 9: Pasto (Y = 450)
            pygame.draw.rect(pantalla, COLORES_BLOQUES[1], (bx, ALTURA_SUELO, TAMANIO_BLOQUE, TAMANIO_BLOQUE))
            pygame.draw.rect(pantalla, (50, 50, 50), (bx, ALTURA_SUELO, TAMANIO_BLOQUE, TAMANIO_BLOQUE), 1)
            
            # Dibujar Filas Inferiores: Piedra Subterránea
            for fila_subte in range(1, 5):
                by = ALTURA_SUELO + (fila_subte * TAMANIO_BLOQUE)
                pygame.draw.rect(pantalla, COLORES_BLOQUES[2], (bx, by, TAMANIO_BLOQUE, TAMANIO_BLOQUE))
                pygame.draw.rect(pantalla, (50, 50, 50), (bx, by, TAMANIO_BLOQUE, TAMANIO_BLOQUE), 1)

        # 2. Decoraciones fijas (Lagos, árboles, rocas, tiendas)
        for l in lagos:
            lx = l["x"] - dist_rec + pj_real_x
            if -400 < lx < ANCHO:
                if IMG["lago"]: pantalla.blit(IMG["lago"], (lx, l["y"]))
                else: pygame.draw.rect(pantalla, (40, 100, 200), (lx, l["y"], 400, 100))
                
        for o in entorno:
            ox = o["x"] - dist_rec + pj_real_x
            if -100 < ox < ANCHO:
                if IMG[o["t"]]: pantalla.blit(IMG[o["t"]], (ox, o["y"]))
                else: 
                    col = (34, 110, 34) if o["t"] == "arbol" else (100, 100, 100)
                    h_rec = 110 if o["t"] == "arbol" else 55
                    pygame.draw.rect(pantalla, col, (ox, o["y"], 60, h_rec))
                    
        for b in bases:
            bx = b["x"] - dist_rec + pj_real_x
            if -100 < bx < ANCHO:
                if IMG["vendedor"]: pantalla.blit(IMG["vendedor"], (bx, b["y"]))
                else: pygame.draw.rect(pantalla, (210, 105, 30), (bx, b["y"], 60, 90))

        # 3. Proyectiles
        for proj in proyectiles:
            pygame.draw.rect(pantalla, (255, 140, 0), (proj[0], proj[1], 15, 6))

        # 4. Enemigos
        for e in enemigos:
            if not e["v"]: continue
            ex_pantalla = e["x"] - dist_rec + pj_real_x
            if -100 < ex_pantalla < ANCHO:
                if IMG[e["t"]]: pantalla.blit(IMG[e["t"]], (ex_pantalla, e["y"]))
                else: pygame.draw.rect(pantalla, (180, 40, 40), (ex_pantalla, e["y"], 50, 50))
                
                if abs(pj_real_x - ex_pantalla) < 40 and abs(pj_real_y - e["y"]) < 50: 
                    hp -= 0.4
                    if hp <= 0: reset_stats(); lanzar_aviso("HAS MUERTO")

        # 5. Personaje
        if IMG[genero_actual]:
            pantalla.blit(IMG[genero_actual], (pj_real_x, pj_real_y))
        else:
            pygame.draw.rect(pantalla, (50, 50, 200), (pj_real_x, pj_real_y, pj_ancho, pj_alto))

        # --- INTERFAZ ---
        for i in range(9):
            r = pygame.Rect(23
