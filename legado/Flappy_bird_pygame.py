import sys
import pygame

# Inicializar Pygame
pygame.init()

# Dimensiones de la ventana
ANCHO = 400
ALTO = 600
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Flappy Bird en Python")

# Control de los FPS (fotogramas por segundo)
reloj = pygame.time.Clock()

# Colores (RGB)
AZUL_CIELO = (135, 206, 235)
VERDE = (34, 139, 34)
AMARILLO = (255, 255, 0)
NEGRO = (0, 0, 0)

# Bucle principal del juego
while True:
  # 1. Manejo de eventos (teclado, cerrar ventana, etc.)
  for evento in pygame.event.get():
    if evento.type == pygame.QUIT:
      pygame.quit()
      sys.exit()

    # Detectar cuando se presiona la barra espaciadora o el click
    if evento.type == pygame.KEYDOWN:
      if evento.key == pygame.K_SPACE:
        print("¡El pájaro salta!")  # Aquí pondremos la física del salto

  # 2. Lógica del juego (actualizar posiciones, colisiones, etc.)

  # 3. Dibujar en la pantalla
  pantalla.fill(AZUL_CIELO)  # Fondo de cielo

  # Dibujar un "pájaro" temporal (un rectángulo amarillo)
  pygame.draw.rect(
      pantalla, AMARILLO, (50, ALTO // 2, 30, 30)
  )  # x, y, ancho, alto

  # Actualizar la pantalla
  pygame.display.flip()

  # Mantener los fotogramas por segundo (ej. 60 FPS)
  reloj.tick(60)