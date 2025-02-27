import pygame
import os
import random
import math

pygame.init()
# setup font
FONT = pygame.font.SysFont('Arial', 16)

# GAME VARIABLES
BG = (23, 21, 59)
WHITE = (255, 255, 255)
CLOCK = pygame.time.Clock()
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500
FPS = 60
# Brick color
BRICK_COLOR = (255, 0, 0)
BRICK_WIDTH = 80
BRICK_HEIGHT = 20

BRICK_COLORS = {
    1: (255, 200, 200),  # Light red - 1 hit
    2: (255, 100, 100),  # Medium red - 2 hits
    3: (255, 0, 0),      # Dark red - 3 hits
}


# Sound files
BOUNCE_SOUND = pygame.mixer.Sound("sounds/bounce.wav")

class Paddle():
    def __init__(self,x,y,width,height):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.base_speed = 5  # Base paddle speed
        self.speed = self.base_speed
        self.rect = pygame.Rect(self.x,self.y,self.width,self.height)

    def move(self,ball_speed):
        key = pygame.key.get_pressed()
        # Only allow left/right movement for breakout game
        # Adjust paddle speed based on ball speed
        self.speed = self.base_speed * (ball_speed / 4)  # 4 is initial ball speed
        if key[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.move_ip(-self.speed,0)
        if key[pygame.K_RIGHT] and self.rect.right < WINDOW_WIDTH:
            self.rect.move_ip(self.speed,0)

    def draw(self,screen,color=WHITE):
        pygame.draw.rect(screen, color, self.rect)

class Ball():
    def __init__(self,x,y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 8
        self.base_speed = 4
        self.speed_x = self.base_speed
        self.speed_y = -self.base_speed  # Start moving upward
        self.rect = pygame.Rect(self.x,self.y,self.radius*2,self.radius*2)
        self.in_play = False
    
    def draw(self,screen,color=WHITE):
        pygame.draw.circle(screen, color,(self.rect.x + self.radius, self.rect.y + self.radius), self.radius)

    def reset(self, paddle):
        # Reset ball position to the middle of paddle
        self.rect.x = paddle.rect.x + (paddle.width // 2) - self.radius
        self.rect.y = paddle.rect.y - (self.radius * 2)
        self.speed_x = self.base_speed
        self.speed_y = -self.base_speed
        self.in_play = False

    def move(self, paddle):
        if not self.in_play:
            # Keep ball on paddle until space is pressed
            self.rect.x = paddle.rect.x + (paddle.width // 2) - self.radius
            self.rect.y = paddle.rect.y - (self.radius * 2)
            return True

        # Wall collisions - IMPROVED BOUNDARY CHECKS
        if self.rect.left <= 0:
            self.rect.left = 0  # Force ball to stay within boundary
            self.speed_x = abs(self.speed_x)  # Ensure it bounces right
        elif self.rect.right >= WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH  # Force ball to stay within boundary
            self.speed_x = -abs(self.speed_x)  # Ensure it bounces left
        if self.rect.top <= 0:
            self.rect.top = 0  # Force ball to stay within boundary
            self.speed_y = abs(self.speed_y)  # Ensure it bounces down
        
        # Ball fell below paddle
        if self.rect.bottom >= WINDOW_HEIGHT:
            self.reset(paddle)
            return False

        if self.rect.colliderect(paddle.rect):
            BOUNCE_SOUND.play()

            # Find intersection point relative to paddle center
            relative_intersect_x = (paddle.rect.x + (paddle.width / 2)) - (self.rect.x + self.radius)
            normalized_intersect = relative_intersect_x / (paddle.width / 2)

            # Convert to bounce angle in radians
            bounce_angle = math.radians(normalized_intersect * 60)  # Max 60-degree bounce

            # Adjust ball velocity based on bounce angle
            self.speed_x = self.base_speed * math.sin(bounce_angle)
            self.speed_y = -self.base_speed * math.cos(bounce_angle)  # Always bounce upward

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        return True

class Bricks():
    def __init__(self):
        self.bricks = []
        self.level = 1
        self.init_bricks()
        
    def init_bricks(self):
        self.bricks = []
        for row in range(6):
            for col in range(6):
                brick_x = col * (BRICK_WIDTH + 10) + 50
                brick_y = row * (BRICK_HEIGHT + 10) + 50
                # Higher rows have more health
                health = min(3, row + self.level)
                # 10% chance for a powerup brick
                
                self.bricks.append({
                    'rect': pygame.Rect(brick_x, brick_y, BRICK_WIDTH, BRICK_HEIGHT),
                    'health': health,
                    
                })

    def draw(self, window):
        for brick in self.bricks:
            # Choose color based on brick health
            color =  BRICK_COLORS[brick['health']]
            pygame.draw.rect(window, color, brick['rect'])

    
    def check_collision(self, ball):
        for brick in self.bricks[:]:
            if ball.rect.colliderect(brick['rect']):
                brick['health'] -= 1
                if brick['health'] <= 0:
                    self.bricks.remove(brick)
                    
                
                if abs(ball.rect.bottom - brick['rect'].top) < 10 or abs(ball.rect.top - brick['rect'].bottom) < 10:
                    ball.speed_y *= -1
                else:
                    ball.speed_x *= -1
                
                return True
            
        return False


class Game():
    def __init__(self,width,height,title,bgColor,font):
        self.width = width
        self.height = height
        self.title = title
        self.bg = bgColor
        self.font = font
        self.surface = None
        self.running = True
        self.surface = pygame.display.set_mode((self.width,self.height))
        pygame.display.set_caption(self.title)

        self.player_paddle = Paddle(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT - 50, 100, 20)
        self.ball = Ball(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 70)
        self.bricks = Bricks()
        self.score = 0
        self.level = 1
        
        # New features
        self.lives = 3
        self.game_over = False
        self.speed_counter = 0
        self.initial_ball_speed = 4  # Save initial speed for reset

    def draw_board(self):
        self.surface.fill(self.bg)

    def draw_text(self,text, text_col, x, y):
        img = self.font.render(text, True, text_col)
        self.surface.blit(img, (x, y))
        
    def draw_lives(self):
        # Draw lives as small circles
        for i in range(self.lives):
            pygame.draw.circle(self.surface, WHITE, (WINDOW_WIDTH - 20 - (i * 20), 20), 5)

    def reset_level(self):
        self.ball.base_speed = self.initial_ball_speed + (self.level - 1) * 0.5
        self.ball.reset(self.player_paddle)
        self.speed_counter = 0

    def show_game_over(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with alpha
        self.surface.blit(overlay, (0, 0))
        
        # Game over text
        font_big = pygame.font.SysFont('Arial', 36)
        game_over_text = font_big.render("GAME OVER", True, WHITE)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = self.font.render("Press R to restart", True, WHITE)
        
        self.surface.blit(game_over_text, (WINDOW_WIDTH//2 - game_over_text.get_width()//2, WINDOW_HEIGHT//2 - 50))
        self.surface.blit(score_text, (WINDOW_WIDTH//2 - score_text.get_width()//2, WINDOW_HEIGHT//2))
        self.surface.blit(restart_text, (WINDOW_WIDTH//2 - restart_text.get_width()//2, WINDOW_HEIGHT//2 + 40))

    def restart_game(self):
        self.lives = 3
        self.score = 0
        self.level = 1
        self.game_over = False
        self.speed_counter = 0
        self.ball.base_speed = self.initial_ball_speed
        self.bricks.level = 1
        self.bricks.init_bricks()
        self.ball.reset(self.player_paddle)

    def run(self):
        while self.running:
            CLOCK.tick(FPS)
            self.draw_board()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.ball.in_play and not self.game_over:
                        self.ball.in_play = True
                    if event.key == pygame.K_r and self.game_over:
                        self.restart_game()

            # Update game objects if not game over
            if not self.game_over:
                self.player_paddle.move(self.ball.base_speed)
                ball_alive = self.ball.move(self.player_paddle)
                
                if not ball_alive:
                    # Player lost a life
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                
                if self.ball.in_play:
                    # Check for speed increase based on counter
                    self.speed_counter += 1
                    if self.speed_counter >= 500:
                        self.ball.base_speed += 0.5
                        self.speed_counter = 0
                
                if self.bricks.check_collision(self.ball):
                    self.score += 10
            
                # Check win condition
                if not self.bricks.bricks:
                    self.level += 1
                    self.bricks.level = self.level
                    self.draw_text(f"LEVEL {self.level}!", WHITE, WINDOW_WIDTH//2 - 40, WINDOW_HEIGHT//2)
                    pygame.display.update()
                    pygame.time.wait(2000)
                    self.bricks.init_bricks()
                    self.reset_level()
            
            # Draw everything
            self.player_paddle.draw(self.surface)
            self.bricks.draw(self.surface)
            self.ball.draw(self.surface)
            
            # Draw score, level, lives
            self.draw_text(f"Score: {self.score}", WHITE, 10, 10)
            self.draw_text(f"Level: {self.level}", WHITE, 100, 10)
            self.draw_text(f"Speed: {self.ball.base_speed:.1f}", WHITE, 200, 10)
            self.draw_lives()
            
            # Show game over screen if game is over
            if self.game_over:
                self.show_game_over()

            pygame.display.update()

        pygame.quit()

if __name__ == "__main__":
    game = Game(WINDOW_WIDTH,WINDOW_HEIGHT,"Breakout",BG,FONT)
    game.run()