

import pygame
import random
import sys

# ===================================================================
# === PARTIE JULIEN & ADRIEN : Bilan Carbone du jeu               ===
# Jeu codé sans assets externes (images/sons) pour réduire le poids,
# la consommation de RAM et l'empreinte carbone globale du projet !
# ===================================================================

# === PARTIE PHILEAS : Créer la fenêtre Pygame et afficher le fond d'écran ===
pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Eco Arcade - Édition Complète (Travail de Groupe)")
clock = pygame.time.Clock()

# === PARTIE HUGO & KARL : Menu des jeux et transitions ===
etat_jeu = "MENU"  # Gère l'écran actuel ("MENU", "OCEAN", "JUNGLE", "ESPACE")


def dessiner_fond(couleur):
    screen.fill(couleur)


def ecran_game_over(score, nom_jeu):
    """Affiche un écran de fin et ramène au menu"""
    global etat_jeu
    dessiner_fond((0, 0, 0))
    font_go = pygame.font.Font(None, 74)
    font_score = pygame.font.Font(None, 40)

    texte_go = font_go.render("GAME OVER", True, (255, 50, 50))
    texte_score = font_score.render(f"Score final ({nom_jeu}) : {score}", True, (255, 255, 255))

    screen.blit(texte_go, (W // 2 - texte_go.get_width() // 2, H // 2 - 50))
    screen.blit(texte_score, (W // 2 - texte_score.get_width() // 2, H // 2 + 30))

    pygame.display.flip()
    pygame.time.delay(3000)  # Pause de 3 secondes avant retour au menu
    etat_jeu = "MENU"


# === PARTIE JULIEN & PHILEAS : Créer l'écran de Menu Principal ===
def menu_principal():
    global etat_jeu
    font_titre = pygame.font.Font(None, 74)
    font_menu = pygame.font.Font(None, 40)

    while etat_jeu == "MENU":
        dessiner_fond((20, 30, 50))

        titre = font_titre.render("ECO ARCADE", True, (255, 255, 255))
        btn_ocean = font_menu.render("1. Océan (Grappin)", True, (100, 200, 255))
        btn_jungle = font_menu.render("2. Jungle (Voiture)", True, (100, 255, 100))
        btn_espace = font_menu.render("3. Espace (Lasers)", True, (255, 100, 100))
        btn_quitter = font_menu.render("ESC. Quitter", True, (150, 150, 150))

        screen.blit(titre, (W // 2 - titre.get_width() // 2, 80))
        screen.blit(btn_ocean, (W // 2 - btn_ocean.get_width() // 2, 220))
        screen.blit(btn_jungle, (W // 2 - btn_jungle.get_width() // 2, 290))
        screen.blit(btn_espace, (W // 2 - btn_espace.get_width() // 2, 360))
        screen.blit(btn_quitter, (W // 2 - btn_quitter.get_width() // 2, 450))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    etat_jeu = "OCEAN"
                elif event.key == pygame.K_2:
                    etat_jeu = "JUNGLE"
                elif event.key == pygame.K_3:
                    etat_jeu = "ESPACE"
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        pygame.display.flip()
        clock.tick(60)


# === PARTIE ADRIEN : Coder le déplacement gauche/droite des véhicules ===
def deplacer_vehicule(x, vitesse, touches, limite_gauche, limite_droite, largeur):
    if touches[pygame.K_LEFT] and x > limite_gauche:
        x -= vitesse
    if touches[pygame.K_RIGHT] and x < limite_droite - largeur:
        x += vitesse
    return x


# === PARTIE JULIEN : Coder l'apparition aléatoire des déchets etc. ===
def apparaitre_objet(liste, proba, type_obj, min_x, max_x, min_y, max_y):
    if random.random() < proba:
        liste.append({
            "x": random.randint(min_x, max_x),
            "y": random.randint(min_y, max_y),
            "type": type_obj
        })


def deplacer_objets_vertical(liste, vitesse):
    for obj in liste[:]:
        obj["y"] += vitesse
        if obj["y"] > H + 50:
            liste.remove(obj)


# ===================================================================
# JEU 1 : OCÉAN (Hugo : Grappin / Karl : Collisions)
# ===================================================================
def jeu_ocean():
    global etat_jeu
    bateau_x, bateau_y = W // 2, 50
    grappin_y = bateau_y + 20
    etat_grappin = "repos"
    grappin_x_fixe = bateau_x + 15
    dechets, poissons = [], []
    score, vies = 0, 3

    while etat_jeu == "OCEAN":
        dessiner_fond((50, 150, 200))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: etat_jeu = "MENU"
                if event.key == pygame.K_SPACE and etat_grappin == "repos":
                    etat_grappin = "descend"
                    grappin_x_fixe = bateau_x + 15

        touches = pygame.key.get_pressed()
        bateau_x = deplacer_vehicule(bateau_x, 6, touches, 0, W, 50)

        # Hugo : Grappin
        if etat_grappin == "repos":
            grappin_y = bateau_y + 20
            grappin_x_fixe = bateau_x + 15
        elif etat_grappin == "descend":
            grappin_y += 7
            if grappin_y > H - 30: etat_grappin = "remonte"
        elif etat_grappin == "remonte":
            grappin_y -= 7
            if grappin_y <= bateau_y + 20: etat_grappin = "repos"

        # Julien : Apparition (Défilement horizontal)
        apparaitre_objet(dechets, 0.02, "dechet", W, W + 50, 150, H - 50)
        apparaitre_objet(poissons, 0.03, "poisson", W, W + 50, 150, H - 50)

        for d in dechets[:]:
            d["x"] -= 3
            if d["x"] < -50: dechets.remove(d)
        for p in poissons[:]:
            p["x"] -= 4
            if p["x"] < -50: poissons.remove(p)

        # Karl : Collisions
        if etat_grappin == "descend":
            rect_grappin = pygame.Rect(grappin_x_fixe, grappin_y, 20, 20)
            for d in dechets[:]:
                if rect_grappin.colliderect(pygame.Rect(d["x"], d["y"], 30, 30)):
                    dechets.remove(d)
                    score += 10
                    etat_grappin = "remonte"
            for p in poissons[:]:
                if rect_grappin.colliderect(pygame.Rect(p["x"], p["y"], 40, 20)):
                    vies -= 1
                    etat_grappin = "remonte"

        if vies <= 0:
            ecran_game_over(score, "Océan")
            continue

        # --- Dessin ---
        pygame.draw.rect(screen, (100, 100, 100), (bateau_x, bateau_y, 50, 20))
        point_attache_x = bateau_x + 25 if etat_grappin == "repos" else grappin_x_fixe + 10
        pygame.draw.line(screen, (255, 255, 255), (bateau_x + 25, bateau_y + 20), (point_attache_x, grappin_y), 2)
        pygame.draw.rect(screen, (40, 40, 40), (point_attache_x - 10, grappin_y, 20, 20))

        for d in dechets: pygame.draw.rect(screen, (139, 69, 19), (d["x"], d["y"], 30, 30))
        for p in poissons: pygame.draw.ellipse(screen, (255, 165, 0), (p["x"], p["y"], 40, 20))

        screen.blit(pygame.font.Font(None, 36).render(f"Score: {score} | Vies: {vies}", True, (255, 255, 255)),
                    (10, 10))
        pygame.display.flip()
        clock.tick(60)


# ===================================================================
# JEU 2 : JUNGLE (Nouveau - Restauré à partir de la V2)
# ===================================================================
def jeu_jungle():
    global etat_jeu
    route_x, route_w = 200, 400  # La route est au milieu
    voiture_x, voiture_y = W // 2 - 30, H - 100
    dechets, singes = [], []
    score, vies = 0, 3
    defilement_lignes = 0

    while etat_jeu == "JUNGLE":
        dessiner_fond((34, 139, 34))  # Fond vert jungle

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: etat_jeu = "MENU"

        touches = pygame.key.get_pressed()
        voiture_x = deplacer_vehicule(voiture_x, 8, touches, route_x, route_x + route_w, 60)

        # Animation de la route
        defilement_lignes += 5
        if defilement_lignes >= 40: defilement_lignes = 0

        # Apparition
        apparaitre_objet(dechets, 0.03, "dechet", route_x + 20, route_x + route_w - 50, -50, -10)
        apparaitre_objet(singes, 0.02, "singe", route_x + 20, route_x + route_w - 50, -50, -10)

        deplacer_objets_vertical(dechets, 5)
        deplacer_objets_vertical(singes, 6)  # Les singes vont un peu plus vite

        # Collisions
        rect_voiture = pygame.Rect(voiture_x, voiture_y, 60, 80)
        rect_bac_avant = pygame.Rect(voiture_x + 10, voiture_y - 10, 40, 20)  # Le bac pour attraper

        for d in dechets[:]:
            rect_d = pygame.Rect(d["x"], d["y"], 30, 30)
            if rect_bac_avant.colliderect(rect_d) or rect_voiture.colliderect(rect_d):
                dechets.remove(d)
                score += 15

        for s in singes[:]:
            rect_s = pygame.Rect(s["x"], s["y"], 40, 40)
            if rect_voiture.colliderect(rect_s):
                singes.remove(s)
                vies -= 1

        if vies <= 0:
            ecran_game_over(score, "Jungle")
            continue

        # --- Dessin ---
        pygame.draw.rect(screen, (50, 50, 50), (route_x, 0, route_w, H))  # Route grise
        pygame.draw.line(screen, (255, 255, 255), (route_x, 0), (route_x, H), 4)  # Bordure
        pygame.draw.line(screen, (255, 255, 255), (route_x + route_w, 0), (route_x + route_w, H), 4)

        # Lignes pointillées de la route
        for y in range(-40 + defilement_lignes, H, 80):
            pygame.draw.rect(screen, (255, 255, 255), (W // 2 - 5, y, 10, 40))

        # Voiture et bac
        pygame.draw.rect(screen, (0, 100, 255), rect_voiture)  # Voiture bleue
        pygame.draw.rect(screen, (200, 200, 200), rect_bac_avant)  # Bac avant

        for d in dechets: pygame.draw.rect(screen, (139, 69, 19), (d["x"], d["y"], 30, 30))
        for s in singes: pygame.draw.circle(screen, (101, 67, 33), (d["x"] + 20, d["y"] + 20), 20)  # Singe marron

        screen.blit(pygame.font.Font(None, 36).render(f"Score: {score} | Vies: {vies}", True, (255, 255, 255)),
                    (10, 10))
        pygame.display.flip()
        clock.tick(60)


# ===================================================================
# JEU 3 : ESPACE (Karl & Adrien)
# ===================================================================
def jeu_espace():
    global etat_jeu
    vaisseau_x, vaisseau_y = W // 2, H - 70
    lasers, debris = [], []
    score, vies = 0, 3

    while etat_jeu == "ESPACE":
        dessiner_fond((10, 10, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: etat_jeu = "MENU"
                if event.key == pygame.K_SPACE:
                    lasers.append({"x": vaisseau_x + 17, "y": vaisseau_y})

        touches = pygame.key.get_pressed()
        vaisseau_x = deplacer_vehicule(vaisseau_x, 7, touches, 0, W, 40)

        for l in lasers[:]:
            l["y"] -= 10
            if l["y"] < 0: lasers.remove(l)

        apparaitre_objet(debris, 0.04, "debris", 20, W - 40, -40, -10)
        deplacer_objets_vertical(debris, 4)

        rect_vaisseau = pygame.Rect(vaisseau_x, vaisseau_y, 40, 40)
        for d in debris[:]:
            rect_debris = pygame.Rect(d["x"], d["y"], 30, 30)

            if rect_vaisseau.colliderect(rect_debris):
                debris.remove(d)
                vies -= 1

            for l in lasers[:]:
                if rect_debris.colliderect(pygame.Rect(l["x"], l["y"], 6, 15)):
                    score += 20
                    if l in lasers: lasers.remove(l)
                    if d in debris: debris.remove(d)
                    break

        if vies <= 0:
            ecran_game_over(score, "Espace")
            continue

        # --- Dessin ---
        pygame.draw.polygon(screen, (0, 255, 255), [(vaisseau_x + 20, vaisseau_y), (vaisseau_x, vaisseau_y + 40),
                                                    (vaisseau_x + 40, vaisseau_y + 40)])
        for l in lasers: pygame.draw.rect(screen, (255, 255, 0), (l["x"], l["y"], 6, 15))
        for d in debris: pygame.draw.circle(screen, (150, 150, 150), (d["x"] + 15, d["y"] + 15), 15)

        screen.blit(pygame.font.Font(None, 36).render(f"Score: {score} | Vies: {vies}", True, (255, 255, 255)),
                    (10, 10))
        pygame.display.flip()
        clock.tick(60)


# ===================================================================
# BOUCLE PRINCIPALE (Lancement du jeu)
# ===================================================================
if __name__ == "__main__":
    while True:
        if etat_jeu == "MENU":
            menu_principal()
        elif etat_jeu == "OCEAN":
            jeu_ocean()
        elif etat_jeu == "JUNGLE":
            jeu_jungle()
        elif etat_jeu == "ESPACE":
            jeu_espace()