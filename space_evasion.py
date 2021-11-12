import pygame                           # Main game library
from pygame import mixer                # Game sounds
from time import sleep                  # Meh, wait some time
from random import randint              # Generating random values
from configparser import ConfigParser   # Loading/saving data
from sys import exit as sysquit         # Quitting process
from os import path, name as os         # OS-stuff
from math import sqrt, ceil             # Some math

pygame.font.init()

WIDTH, HEIGHT = 880, 660
DISPLAY = pygame.display.set_mode((WIDTH, HEIGHT))

color1 = (44, 72, 143)      #Blue
color2 = (57, 115, 173)     #Blue
color3 = (83, 172, 204)     #Blue
color4 = (180, 180, 180)    #White
color5 = (179, 68, 40)      #Red
color6 = (209, 102, 48)     #Red
color7 = (230, 141, 62)     #Orange
color8 = (19, 19, 19)       #Black
color9 = (21, 21, 21)       #Black
color10 = (23, 23, 23)      #Dark gray

path = path.dirname(path.realpath(__file__))
sep = '\\' if os == 'nt' else '/'
img_path = f'{path}{sep}img'
data_path = f'{path}{sep}data'
sound_path = f'{path}{sep}sound'
font_name = f'{path}{sep}font{sep}beleren_bold.ttf'

img = pygame.image.load(f'{img_path}{sep}main_bg.png')
img = pygame.transform.scale(img, (WIDTH, HEIGHT))
DISPLAY.blit(img, (0,0))
font = pygame.font.Font(font_name, 90)
loading = font.render('Loading', False, color4)
tw,th=font.size('Loading')
DISPLAY.blit(loading, (WIDTH//2-tw//2,HEIGHT//2-th))
pygame.display.update()
del font, loading, tw, th, img

def quit_game():
    with open(f'{data_path}{sep}data.ini', 'w+') as file:
        data = f'[data]\nhighscore = {highscore}\nplays = {plays}'
        file.write(data)
    pygame.quit()
    sysquit()

def draw_cursor():
    if is_drawing_cursor:
        mouse_pos = pygame.mouse.get_pos()
        DISPLAY.blit(cursor, (mouse_pos[0]-cursor_size//2, mouse_pos[1]-cursor_size//2))

def reset_mouse_pos():
    pygame.mouse.set_pos(WIDTH//2-cursor_size//2, HEIGHT//2-cursor_size//2)

def get_distance(sprite1, sprite2):
    a = (sprite2.x+sprite2.width//2) - (sprite1.x+sprite1.width//2) 
    b = (sprite2.y+sprite2.height//2) - (sprite1.y+sprite1.height//2)
    c = a**2 + b**2
    return round(sqrt(c),2)

def screen_animation(next_screen):
    surface_amt = 10
    surface_width = 0
    surface_height = HEIGHT//surface_amt

    while surface_width <= WIDTH//surface_amt:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

        surfaces = [
            [
                pygame.Surface((surface_width, surface_height)) for j in range(surface_amt)
            ] for i in range(surface_amt)
        ]

        for row, line in enumerate(surfaces):
            for index, surface in enumerate(line):
                surface.fill(color10 if (row+index)%2==0 else color9)
                DISPLAY.blit(surface, (index*(WIDTH//surface_amt), row*surface_height))
    
        surface_width += 1
        CLOCK.tick(FPS*8)
        pygame.display.update()

    next_screen()

FPS = 24
pygame.display.set_icon(pygame.transform.scale(
        pygame.image.load(f'{img_path}{sep}player.png'), (64,64)))
CLOCK = pygame.time.Clock()
score, highscore = 0, 0
config = ConfigParser()
config.read(f'{data_path}{sep}data.ini')
try: highscore = int(config['data']['highscore'])
except: highscore = 0
plays = 0
try: plays = int(config['data']['plays'])
except: plays = 0
cursor_size = 12
is_drawing_cursor = False
pygame.display.set_caption('Space evasion')
pygame.mouse.set_visible(False)
cursor = pygame.image.load(f'{img_path}{sep}cursor.png')
cursor = pygame.transform.scale(cursor, (cursor_size, cursor_size))
mixer.init()
playing_menu_song = False
mixer.Channel(0).set_volume(0.15)   # Background music
mixer.Channel(1).set_volume(0.40)   # Clicks || Other
mixer.Channel(2).set_volume(0.05)   # FXs for main game
mixer.Channel(3).set_volume(0.10)   # Laser layer 1
mixer.Channel(4).set_volume(0.10)   # Laser layer 2
mixer.Channel(5).set_volume(0.00)   # Changes vol while playing
menu_background_song = mixer.Sound(f'{sound_path}{sep}menu_bg.mp3')
game_background_song = mixer.Sound(f'{sound_path}{sep}game_bg.mp3')
click_sound = mixer.Sound(f'{sound_path}{sep}click.wav')
death_sound = mixer.Sound(f'{sound_path}{sep}dead.wav')
hurt_sound = mixer.Sound(f'{sound_path}{sep}hurt.wav')
laser_sound_deep = mixer.Sound(f'{sound_path}{sep}laser1.wav')
laser_sound_high = mixer.Sound(f'{sound_path}{sep}laser2.wav')
nearby_bullet_sound = mixer.Sound(f'{sound_path}{sep}nearby.wav')
boost_sound = mixer.Sound(f'{sound_path}{sep}boost.wav')
hp_sound = mixer.Sound(f'{sound_path}{sep}hp.wav')

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = 48
        self.height = 48
        self.ow = self.width
        self.oh = self.height
        self.hp = 3
        self.max_hp = 5
        self.x = WIDTH//2 - self.width//2
        self.y = HEIGHT//2 - self.height//2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.image = pygame.image.load(f'{img_path}{sep}player.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.dimage = self.image.copy()
        self.original_speed = 5
        self.speed = self.original_speed
        self.slow_speed = 1
        self.has_moved = False
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = [(self.x+self.width//3, self.y+self.height//3)]
        self.particle_frames = [0]
        self.particle_amt = 100
        self.particle_decay = 8
        self.particle_size = 8
        self.rotation = 'up'
        self.fuel_percent = 100
        self.fuel_lose_rate = 0.2
        self.fuel_regen_rate = 0.1

    def rotate(self, dir):
        if dir == 'up':
            self.image = self.dimage
            self.rect = self.image.get_rect()
            self.width, self.height = self.ow, self.oh
        elif dir == 'down':
            self.image = pygame.transform.rotate(self.dimage, 180)
            self.rect = self.image.get_rect()
            self.width, self.height = self.ow, self.oh
        elif dir == 'right':
            self.image = pygame.transform.rotate(self.dimage, 270)
            self.width, self.height = self.oh, self.ow
        elif dir == 'left':
            self.image = pygame.transform.rotate(self.dimage, 90)
            self.width, self.height = self.oh, self.ow

        self.mask = pygame.mask.from_surface(self.image)
        self.rotation = dir

    def update(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if self.rotation in ['up', 'down']:
            self.width, self.height = self.width, self.height
        elif self.rotation in ['left', 'right']:
            self.width, self.height = self.height, self.width

    def draw(self):
        self.update()
        DISPLAY.blit(self.image, (self.x, self.y))
    
    def update_pos(self):
        while len(self.particles) >= self.particle_amt:
            self.particles.pop(0)
        self.particles.append((self.x, self.y))
        self.particle_frames.append(0)

    def draw_particles(self):
        for index, pos in enumerate(self.particles):
            if self.particle_frames[index] < self.particle_decay:
                particle = pygame.Surface((self.particle_size, self.particle_size))
                particle.fill([color1, color2, color3][randint(0,2)])
                x = pos[0]+self.width//2-self.particle_size//2+randint(-self.width//4, self.width//4)
                y = pos[1]+self.height//2-self.particle_size//2+randint(-self.height//4,self.height//4)
                DISPLAY.blit(particle, (x, y))
                self.particle_frames[index] += 1
            else:
                self.particles.pop(index)
                self.particle_frames.pop(index)

    def draw_shield(self):
        surf = pygame.image.load(f'{img_path}{sep}shield.png').convert_alpha()
        size = (self.width+self.height)//2+12
        surf = pygame.transform.scale(surf, (size, size))
        surf.set_alpha(255//3)
        DISPLAY.blit(surf, (self.x-6, self.y-6))

    def die(self):
        sleep(.2)
        mixer.Channel(5).stop()
        mixer.Channel(2).play(death_sound)
        for i in range(75):
            surface = pygame.Surface((randint(6,10), randint(6,10)))
            surface.fill([color5,color6,color7][randint(0,2)])
            x = self.x+self.width//2 + 2*randint(-self.width*randint(1,4)//4, 
                self.width*randint(1,4)//4)+randint(-15,15)
            y = self.y+self.height//2 + 2*randint(-self.height*randint(1,4)//4, 
                self.height*randint(1,4)//4)+randint(-15,15)
            DISPLAY.blit(surface, (x, y))
            pygame.display.update()
            sleep(5//FPS)
            
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir):
        super().__init__()
        self.width = 16
        self.height = 16        
        self.move_dir = dir
        self.x = x
        self.y = y

        if self.move_dir in ['+x', '-x']:
            self.y = y
            if self.move_dir == '+x':
                self.x = 0
            else:
                self.x = WIDTH
        
        if self.move_dir in ['+y', '-y']:
            self.x = x
            if self.move_dir == '+y':
                self.y = 0
            else:
                self.y = HEIGHT

        self.speed = randint(1, 5)*2
        self.frames = randint(1, 5)
        self.mp = 1 if randint(0, 1)==1 else -1
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.image = pygame.image.load(f'{img_path}{sep}enemy.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.surface = pygame.Surface((self.width, self.height)).convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        self.particles = [(self.x+self.width//3, self.y+self.height//3)]
        self.particle_frames = [0]
        self.particle_amt = 10
        self.particle_decay = 10
        self.particle_size = 4

    def update(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self):
        if self.move_dir in ['+y', '-y']:
            mp = 1 if self.move_dir=='+y' else -1
            self.y += mp * self.speed/self.frames
        else:
            mp = 1 if self.move_dir=='+x' else -1
            self.x += mp * self.speed/self.frames
        
        self.update()
        self.update_pos()

    def check_inside(self):
        if self.x < -self.width or self.x > WIDTH+self.width:
            return False
        if self.y < -self.height or self.y > HEIGHT+self.height:
            return False
        return True 
    
    def draw(self):
        DISPLAY.blit(self.image, (self.x, self.y))
    
    def update_pos(self):
        while len(self.particles) >= self.particle_amt:
            self.particles.pop(0)
        self.particles.append((self.x, self.y))
        self.particle_frames.append(0)
    
    def draw_particles(self):
        for index, pos in enumerate(self.particles):
            if self.particle_frames[index] < self.particle_decay:
                particle = pygame.Surface((self.particle_size, self.particle_size))
                particle.fill([color5, color6, color7][randint(0,2)])
                x = pos[0]+self.width//2-self.particle_size//2+randint(-self.width//3, self.width//3)
                y = pos[1]+self.height//2-self.particle_size//2+randint(-self.height//3,self.height//3)
                DISPLAY.blit(particle, (x, y))
                self.particle_frames[index] += 1
            else:
                self.particles.pop(index)
                self.particle_frames.pop(index)

class Warning(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.size = 20
        self.dir = ['+x', '-x', '+y', '-y'][randint(0,3)]
        if self.dir == '+x':
            self.x = 10
        elif self.dir == '-x':
            self.x = WIDTH-10-self.size
        elif self.dir == '+y':
            self.y = 10
        elif self.dir == '-y':
            self.y = HEIGHT-10-self.size
        self.image = pygame.image.load(f'{img_path}{sep}warning.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = pygame.Rect((self.size, self.size), (self.x, self.y))
        self.show_frames = 30
        self.shown = 0

    def update(self):
        self.shown += 1
        if not self.shown >= self.show_frames:
            self.draw()
            return True
        return False
    
    def draw(self):
        DISPLAY.blit(self.image, (self.x-2, self.y-2))

class Laser(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.width, self.height = 16, 16
        self.ticked, self.decay = 0, randint(FPS*2, FPS*5)
        self.image = pygame.image.load(f'{img_path}{sep}laser.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.warning_image = pygame.image.load(f'{img_path}{sep}warning_laser.png').convert_alpha()
        self.warning_image = pygame.transform.scale(self.warning_image, (self.width, self.height))
        self.alpha_level = 0
        self.warning_image.set_alpha(self.alpha_level)
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = randint(0,1)
        self.is_warning = True
        self.increase_alpha = True

        if self.direction == 0:
            self.x = 0
            self.y = randint(0, HEIGHT-self.width)
            self.width, self.height = self.height, self.width
            self.image = pygame.transform.rotate(self.image, 90)
            self.warning_image = pygame.transform.rotate(self.warning_image, 90)
            
        if self.direction == 1:
            self.y = 0
            self.x = randint(0, WIDTH-self.height)

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if self.direction == 0:
            self.xs = [self.x+self.width*i for i in range(WIDTH//self.height)]
        if self.direction == 1:
            self.ys = [self.y+self.height*i for i in range(HEIGHT//self.height)]
    
    def draw(self):
        if self.direction == 0:
            for x in self.xs:
                if not self.is_warning:
                    DISPLAY.blit(self.image, (x, self.y))
                else:
                    DISPLAY.blit(self.warning_image, (x, self.y))

        elif self.direction == 1:
            for y in self.ys:
                if not self.is_warning:
                    DISPLAY.blit(self.image, (self.x, y))
                else:
                    DISPLAY.blit(self.warning_image, (self.x, y))

    def tick(self):
        global FPS

        if self.alpha_level >= 255:
            self.is_warning = False
            self.increase_alpha = False
        else:
            self.warning_image.set_alpha(self.alpha_level)
        
        if self.increase_alpha:
            self.alpha_level += 255//(FPS*3)

class HPBoost(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.exists = False
        self.height = 40
        self.width = 40
        self.min_sf, self.max_sf = FPS*20, FPS*90
        self.gen_pos()
        self.image = pygame.image.load(f'{img_path}{sep}heart_plus.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.surface = pygame.Surface((self.width, self.height))
        self.mask = pygame.mask.from_surface(self.surface)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.ticked_frames = 0

    def tick(self):
        if not self.exists:
            self.ticked_frames += 1
            if self.ticked_frames > self.spawn_frames:
                self.ticked_frames = 0
                self.exists = True
                self.max_sf -= 10*FPS if self.max_sf >= self.min_sf+10*FPS else 0
        if self.exists:
            self.draw()
    
    def gen_pos(self):
        self.x = randint(0,WIDTH-self.width)
        self.y = randint(0,HEIGHT-self.height)
        self.spawn_frames = randint(self.min_sf, self.max_sf)

    def update(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self): 
        self.update()
        DISPLAY.blit(self.image, (self.x, self.y))

class RandEffect(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.effects = ['speedboost', 'remove', 'remove', 'freeze', 'refuel']
        self.width, self.height = 40, 40
        self.x, self.y = randint(0, WIDTH-self.width), randint(0, HEIGHT-self.height)
        self.image = pygame.image.load(f'{img_path}{sep}rand_effect.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width,self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.surface = pygame.Surface((self.width, self.height))
        self.mask = pygame.mask.from_surface(self.image)
        self.ticked_frames = 0
        self.min_spawn, self.max_spawn = FPS*20, FPS*80
        self.gen_pos()
        self.exists = False
        self.effect_ticks = 0
        self.effect_tf = FPS*5

    def gen_effect(self):
        self.ticked_frames = 0
        self.effect_tf = randint(FPS*1.5, FPS*5)
        return self.effects[randint(0,len(self.effects)-1)]
    
    def gen_pos(self):
        self.x = randint(0, WIDTH-self.width)
        self.y = randint(0, HEIGHT-self.height)
        self.spawn_frames = randint(self.min_spawn, self.max_spawn)

    def update(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.mask = pygame.mask.from_surface(self.image)

    def tick(self):
        if self.exists:
            self.draw()
        else:
            self.ticked_frames += 1
            if self.ticked_frames >= self.spawn_frames:
                self.exists = True
                self.ticked_frames = 0
                self.max_spawn -= 10*FPS if self.max_spawn >= self.min_spawn+10*FPS else 0

    def draw(self):
        self.update()
        DISPLAY.blit(self.image, (self.x, self.y))

def paused():
    paused_font = pygame.font.Font(font_name, 75)
    desc_font = pygame.font.Font(font_name, 35)
    paused_text = paused_font.render('Paused game', False, color4)
    back_text = desc_font.render('Press ESC to play', False, color4)
    ptw, pth = paused_font.size('Paused game')
    btw, bth = desc_font.size('Press ESC to play')
    ptx, pty = WIDTH//2-ptw//2,HEIGHT//2-pth//2
    btx, bty = WIDTH//2-btw//2,HEIGHT//2-bth//2+50

    DISPLAY.blit(paused_text, (ptx, pty))
    DISPLAY.blit(back_text, (btx, bty))
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                if pressed[pygame.K_ESCAPE]:
                    return None
        CLOCK.tick(FPS)

def tutorial():
    reset_mouse_pos()
    global is_drawing_cursor
    is_drawing_cursor = True
    main_menu, play_game, exit_game = False, False, False
    background = pygame.transform.scale(pygame.image.load(f'{img_path}{sep}main_bg.png'), 
        (WIDTH, HEIGHT))
    titel_font = pygame.font.Font(font_name, 65)
    tx, ty = 50, 50
    ttext = titel_font.render('Tutorial', False, color4)
    sub_font = pygame.font.Font(font_name, 35)
    desc_font = pygame.font.Font(font_name, 20)
    text = pygame.Surface((1,1))
    desc = pygame.Surface((1,1))
    tx, ty = 40, HEIGHT//10*5
    dx, dy = 40, HEIGHT//10*6
    ix, iy = 150, 200
    button_font = pygame.font.Font(font_name, 35)
    main_menu_text = button_font.render('Go back', False, color4)
    mmtw, mmth = button_font.size('Go back')
    mmtx = WIDTH-mmtw-30
    mmty = HEIGHT-mmth-30
    main_menu_rect = main_menu_text.get_rect()
    main_menu_rect.x, main_menu_rect.y = mmtx, mmty
    frame = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            
            elif event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                main_menu = pressed[pygame.K_1]
                play_game = pressed[pygame.K_2]
                exit_game = pressed[pygame.K_3]
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = pygame.mouse.get_pressed()
                if state[0]:
                    mixer.Channel(1).play(click_sound)

                    mouse_pos = pygame.mouse.get_pos()
                    if main_menu_rect.collidepoint(mouse_pos):
                        screen_animation(start_menu)
            
        if main_menu: screen_animation(start_menu)
        elif play_game: screen_animation(main)
        elif exit_game: quit_game()

        DISPLAY.blit(background, (0,0))

        texts = [
            'This is you, the player',
            'This is an enemy, watch out',
            'This is a warning',
            'This is a laser, they also hurt',
            'This is a laser charging up',
            'This is a health boost',
            'This is a random effect',
            'This is your life',
            'This is your fuel',
            'Speeeeed',
            'Not speeeed',
            'Score',
            'Highscore',
            'Getting score',
        ]
        descs = [
            'While playing you can move with WASD or the arrow keys',
            'Do not touch, you may take damage',
            'They show where enemies spawn',
            'Caution: very warm',
            'A laser has to charge, avoid being in the line of fire',
            'It gives you an extra life',
            'It gives one random good effect',
            'You start with 3 of them but you can get more from health boosts',
            'It will magically refuel whenever you are idle',
            'This icon shows whenever a speed boost is active',
            'This icon shows whenever a freeze boost is active',
            'The white number is your current score',
            'The blue text is your highscore',
            'You get points whenever enemies disappear',
        ]
        imgs = [
            'player.png', 'enemy.png', 'warning.png', 'laser.png', 'warning_laser.png', 
            'heart_plus.png', 'rand_effect.png', 'heart.png', 'fuel.png', 'speedboost.png', 
            'freezeboost.png',
        ]

        images = [
            pygame.transform.scale(pygame.image.load(f'{img_path}{sep}{img}'), (40,40)) for img in imgs
        ]
        images.append(sub_font.render('42', False, color4)) 
        images.append(sub_font.render('102', False, color1))
        images.append(sub_font.render('+', False, color4))

        if frame > len(texts):
            screen_animation(start_menu)

        text_str = texts[int(frame)]
        desc_str = descs[int(frame)]
        image = images[int(frame)]

        mouse_pos = pygame.mouse.get_pos()
        if main_menu_rect.collidepoint(mouse_pos):
            main_menu_text = button_font.render('Go back', False, color1)
        else:
            main_menu_text = button_font.render('Go back', False, color4)

        text = sub_font.render(text_str, False, color4)
        desc = desc_font.render(desc_str, False, color4)
        DISPLAY.blit(ttext, (40, 50))
        DISPLAY.blit(text, (tx, ty))
        DISPLAY.blit(desc, (dx, dy))
        if imgs[int(frame)] == 'fuel.png':
            image = pygame.transform.scale(image, (150, 20));ix=75
        DISPLAY.blit(image, (ix, iy))
        DISPLAY.blit(main_menu_text, (mmtx, mmty))
        
        draw_cursor()
        ix=150
        CLOCK.tick(20)
        pygame.display.update()
        frame += 0.01

def main():
    reset_mouse_pos()
    global highscore
    global score
    global is_drawing_cursor
    global plays
    is_drawing_cursor = False
    plays += 1
    
    player = Player()
    hp_boost = HPBoost()
    randeffect = RandEffect()
    bullets = []
    warnings = []
    lasers = []
    spawn_rate_frames = FPS*2
    spawn_loop = 0
    spawn_amount = 1
    laser_spawn_loop = 0
    lsr_min, lsr_max = FPS*10, FPS*30
    background_speed = 1/10/FPS
    background_x = 0
    laser_spawn_rate = randint(lsr_min, lsr_max)
    inv_frames = FPS*3
    score = 0
    inv_frames_ticked = 0
    is_inv = False
    effect = 'none'
    move_up, move_left, move_down, move_right = False, False, False, False
    bg_image = pygame.image.load(f'{img_path}{sep}main_bg.png').convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    heart_image = pygame.image.load(f'{img_path}{sep}heart.png').convert_alpha()
    heart_size = 40
    fuel_img = pygame.image.load(f'{img_path}{sep}fuel.png')
    fuel_img = pygame.transform.scale(fuel_img, (150, 20))
    lost_hp = False
    lhptf = FPS*1
    lhpcf = 0
    max_spawn_amt = 5
    effect_img_size = 40
    effect_img_x, effect_img_y = WIDTH-effect_img_size-20, HEIGHT-effect_img_size-20
    speedboost_img = pygame.image.load(f'{img_path}{sep}speedboost.png').convert_alpha()
    speedboost_img = pygame.transform.scale(speedboost_img, (effect_img_size, effect_img_size))
    freeze_img = pygame.image.load(f'{img_path}{sep}freezeboost.png').convert_alpha()
    freeze_img = pygame.transform.scale(freeze_img, (effect_img_size, effect_img_size))
    heart_image = pygame.transform.scale(heart_image, (heart_size, heart_size))
    rftf = FPS*2
    rfcf = 0
    rfsi, rmsi = False, False
    rfimg = pygame.image.load(f'{img_path}{sep}refuel.png').convert_alpha()
    rfimg = pygame.transform.scale(rfimg, (effect_img_size, effect_img_size))
    rmimg = pygame.image.load(f'{img_path}{sep}remove.png').convert_alpha()
    rmimg = pygame.transform.scale(rmimg, (effect_img_size, effect_img_size))
    lost_hp_img = pygame.image.load(f'{img_path}{sep}heart_dmg.png').convert_alpha()
    lost_hp_img = pygame.transform.scale(lost_hp_img, (heart_size, heart_size))
    dmg_effect_surface = pygame.Surface((WIDTH, HEIGHT))
    dmg_effect_surface.set_alpha(255//8)
    dmg_effect_surface.fill(color5)
    playing_laser_sound = False
    score_font = pygame.font.Font(font_name, 50)
    score_str = f'{score}'
    fuel_startup_delay = FPS*2
    fuel_startup_frame = 0
    fuel_delay = False
    hs_font = pygame.font.Font(font_name, 25)
    hs_text = hs_font.render(f'{highscore}', False, color1)

    mixer.Channel(0).play(game_background_song, loops=-1)
    mixer.Channel(5).play(nearby_bullet_sound, loops=-1)

    while True:
        background_x += background_speed
        highscore = score if score > highscore else highscore
        score_text = score_font.render(score_str, False, color4)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
        
            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                move_up = pressed[pygame.K_w]       or pressed[pygame.K_UP]
                move_left = pressed[pygame.K_a]     or pressed[pygame.K_LEFT]
                move_down = pressed[pygame.K_s]     or pressed[pygame.K_DOWN]
                move_right = pressed[pygame.K_d]    or pressed[pygame.K_RIGHT]

                if not player.has_moved:
                    player.has_moved = any([move_up, move_left, move_down, move_right])

                if pressed[pygame.K_3]:
                    quit_game()
                if pressed[pygame.K_ESCAPE]:
                    paused()

            if event.type == pygame.KEYUP:
                pressed = pygame.key.get_pressed()
                move_up = pressed[pygame.K_w]       or pressed[pygame.K_UP]
                move_left = pressed[pygame.K_a]     or pressed[pygame.K_LEFT]
                move_down = pressed[pygame.K_s]     or pressed[pygame.K_DOWN]
                move_right = pressed[pygame.K_d]    or pressed[pygame.K_RIGHT]

        if player.has_moved:
            if player.rotation == 'up':
                player.y -= player.slow_speed if player.y-player.slow_speed >= 0 else 0
            elif player.rotation == 'down':
                player.y += player.slow_speed if player.y+player.slow_speed+player.height <= HEIGHT else 0
            if player.rotation == 'left':
                player.x -= player.slow_speed if player.x-player.slow_speed >= 0 else 0
            elif player.rotation == 'right':
                player.x += player.slow_speed if player.x+player.slow_speed+player.height <= HEIGHT else 0
            player.fuel_percent += player.fuel_regen_rate if player.fuel_percent < 100 else 0

        if fuel_delay:
            if fuel_startup_frame > fuel_startup_delay:
                fuel_delay = False
                fuel_startup_frame = 0
            fuel_startup_frame += 1

        if ceil(player.fuel_percent-player.fuel_regen_rate) > 0 and not fuel_delay:
            if move_left: 
                player.rotate('left')
                player.x -= player.speed  if player.x-player.speed >= 0 else 0
                player.update_pos()
            elif move_right: 
                player.rotate('right')
                player.x += player.speed if player.x+player.speed+player.width <= WIDTH else 0
                player.update_pos()
            if move_up: 
                player.rotate('up')
                player.y -= player.speed  if player.y-player.speed >= 0 else 0
                player.update_pos()
            elif move_down: 
                player.rotate('down')
                player.y += player.speed  if player.y+player.speed+player.height <= HEIGHT else 0
                player.update_pos()

            if any([move_left, move_right, move_up, move_down]):
                player.fuel_percent -= player.fuel_lose_rate
            
            if player.fuel_percent <= 0:
                fuel_delay = True

        if spawn_loop >= spawn_rate_frames:
            spawn_loop = 0
            for i in range(spawn_amount):
                x = randint(0, WIDTH-16)
                y = randint(0, HEIGHT-16)
                warnings.append(Warning(x, y))
            spawn_amount = score//25+1
  
        if laser_spawn_loop >= laser_spawn_rate:
            laser_spawn_loop = 0
            lasers.append(Laser())
            lsr_min -= spawn_amount*5 if lsr_min > FPS else 0
            lsr_max -= spawn_amount*5 if lsr_max > FPS*3 else 0
            laser_spawn_rate = randint(lsr_min, lsr_max)

        if background_x >= WIDTH:
            background_x = 0

        DISPLAY.blit(bg_image, (background_x-WIDTH, 0))

        DISPLAY.blit(bg_image, (background_x, 0))
        player.draw_particles()
        player.draw()

        if player.hp < player.max_hp:
            hp_boost.tick()
            if hp_boost.exists:
                offset_x = player.rect.x - hp_boost.rect.x
                offset_y = player.rect.y - hp_boost.rect.y
                overlap = hp_boost.mask.overlap(player.mask, (offset_x, offset_y))
                if overlap:
                    mixer.Channel(2).play(hp_sound)
                    player.hp += 1
                    hp_boost.exists = False
                    hp_boost.gen_pos()

        randeffect.tick()
        if randeffect.exists:
            offset_x = player.rect.x - randeffect.rect.x
            offset_y = player.rect.y - randeffect.rect.y
            overlap = randeffect.mask.overlap(player.mask, (offset_x, offset_y))
            if overlap:    
                mixer.Channel(2).play(boost_sound)
                randeffect.exists = False
                randeffect.gen_pos()
                effect = randeffect.gen_effect()

        if randeffect.effect_ticks > randeffect.effect_tf+FPS:
            randeffect.effect_ticks = 0
            player.speed = player.original_speed
            effect = 'none'

        else:
            randeffect.effect_ticks += 1
            if effect == 'speedboost':
                player.speed = player.original_speed*2

        if effect != 'freeze':
            for index, warning in enumerate(warnings):
                updated = warning.update()
                if not updated:
                    bullets.append(Bullet(warning.x, warning.y, warning.dir))
                    warnings.pop(index)
        else: 
            for warning in warnings: warning.draw()

        for index, bullet in enumerate(bullets):            
            if effect != 'freeze':
                bullet.move()
            bullet.draw_particles()
            bullet.draw()
            
            offset_x = player.rect.x - bullet.rect.x
            offset_y = player.rect.y - bullet.rect.y
            overlap = bullet.mask.overlap(player.mask, (offset_x, offset_y))

            if overlap:
                if not(is_inv) and inv_frames_ticked == 0:
                    is_inv = True
                    mixer.Channel(2).set_volume(0.40)
                    mixer.Channel(2).play(hurt_sound)
                    player.hp -= 1
                    lost_hp = True
                    if player.hp <= 0:
                        DISPLAY.blit(dmg_effect_surface, (0,0))
                        player.die()
                        sleep(1)
                        screen_animation(game_over)
                
            if not bullet.check_inside():
                bullets.pop(index)
                score += 1
                score_str = f'{score}'  

        min_bullet_distance=WIDTH
        if len(bullets)>0:
            min_bullet_distance = min([get_distance(player, bullet) for bullet in bullets])
        new_volume = min_bullet_distance/WIDTH
        
        mixer.Channel(5).set_volume(1/50-round(new_volume/50,2))

        for index, laser in enumerate(lasers):
            laser.tick()
            laser.draw()

            overlap = False

            if laser.ticked >= laser.decay:
                lasers.pop(index)
                continue
            laser.ticked += not laser.is_warning

            if laser.direction == 0 and not laser.is_warning:
                offset_y = player.rect.y - laser.rect.y
                for x in laser.xs:
                    offset_x = player.rect.x - x
                    overlap = laser.mask.overlap(player.mask, (offset_x, offset_y))
                    if overlap: break
            
            elif laser.direction == 1 and not laser.is_warning:
                offset_x = player.rect.x - laser.rect.x
                for y in laser.ys:
                    offset_y = player.rect.y - y
                    overlap = laser.mask.overlap(player.mask, (offset_x, offset_y))
                    if overlap: break

            if overlap:
                if not(is_inv) and inv_frames_ticked == 0:
                    is_inv = True
                    mixer.Channel(2).set_volume(0.40)
                    mixer.Channel(2).play(hurt_sound)
                    player.hp -= 1
                    lost_hp = True
                    if player.hp <= 0:
                        DISPLAY.blit(dmg_effect_surface, (0,0))
                        player.die()
                        sleep(1)
                        screen_animation(game_over)

        if len(lasers) > 0 and not playing_laser_sound:
            mixer.Channel(3).play(laser_sound_deep, loops=-1)
            mixer.Channel(4).play(laser_sound_high, loops=-1)
            playing_laser_sound = True
        elif len(lasers) == 0 and playing_laser_sound:
            mixer.Channel(3).stop()
            mixer.Channel(4).stop()
            playing_laser_sound = False
        
        if is_inv:
            inv_frames_ticked += 1
            player.draw_shield()
            if inv_frames_ticked > inv_frames:
                is_inv = False
                inv_frames_ticked = 0

        if effect == 'freeze':
            DISPLAY.blit(freeze_img, (effect_img_x, effect_img_y))
        
        if effect == 'speedboost':
            DISPLAY.blit(speedboost_img, (effect_img_x, effect_img_y))

        if effect == 'refuel':
            player.fuel_percent = 100
            rfsi = True
            effect = 'none'
        
        if effect == 'remove':
            bullets = bullets[::2]
            rmsi = True
            effect = 'none'

        if rfsi:
            rfcf += 1
            if rfcf <= rftf:
                DISPLAY.blit(rfimg, (effect_img_x, effect_img_y))
            else:
                rfcf = 0
                rfsi = False

        if rmsi:
            rfcf += 1
            if rfcf <= rftf:
                DISPLAY.blit(rmimg, (effect_img_x, effect_img_y))
            else:
                rfcf = 0
                rmsi = False

        fuel_bar_height = 20
        fuel_bar_x = WIDTH//16-heart_size//2
        fuel_bar_y = HEIGHT//16*15-fuel_bar_height//2-heart_size-10
        fuel_img = pygame.transform.scale(fuel_img, (150, fuel_bar_height))
        fuel_surface = fuel_img.subsurface(0, 0, player.fuel_percent*1.5, fuel_bar_height)
        DISPLAY.blit(fuel_surface, (fuel_bar_x, fuel_bar_y))

        DISPLAY.blit(score_text, (20, 20))
        DISPLAY.blit(hs_text, (20, 65))

        for i in range(player.hp):
            x = WIDTH//16 + (heart_size+10)*i - heart_size//2
            y = HEIGHT//16*15-heart_size//2
            DISPLAY.blit(heart_image, (x, y))

        if lost_hp:
            if lhpcf >= lhptf:
                lost_hp = False
                lhpcf = 0
            else:
                x = WIDTH//16+(heart_size+10)*player.hp - heart_size//2
                y = HEIGHT//16*15 - heart_size//2
                DISPLAY.blit(lost_hp_img, (x, y))
                lhpcf += 1
            if 0 < lhpcf <= FPS//4:
                DISPLAY.blit(dmg_effect_surface, (0,0))

        spawn_loop += 1
        laser_spawn_loop += 1
        spawn_amount = spawn_amount if spawn_amount < max_spawn_amt else max_spawn_amt
        draw_cursor()
        pygame.display.update()
        CLOCK.tick(FPS)

def game_over():
    reset_mouse_pos()
    global highscore
    global is_drawing_cursor
    global playing_menu_song
    is_drawing_cursor = True
    game_over_bg = pygame.image.load(f'{img_path}{sep}main_bg.png').convert()
    game_over_bg = pygame.transform.scale(game_over_bg, (WIDTH, HEIGHT))
    game_over_font = pygame.font.Font(font_name, 65)
    subtitle_font = pygame.font.Font(font_name, 35)

    over_ = game_over_font.render('Game Over', False, color4)
    play_ = subtitle_font.render('Play again', False, color4)
    main_ = subtitle_font.render('Main menu', False, color4)
    quit_ = subtitle_font.render('Exit game', False, color4)
    gx, gy = 40, 40
    px, py = 50, HEIGHT//10*5
    mx, my = 50, HEIGHT//10*6
    qx, qy = 50, HEIGHT//10*7

    play_rect = play_.get_rect()
    play_rect.x, play_rect.y = px, py
    main_rect = main_.get_rect()
    main_rect.x, main_rect.y = mx, my
    quit_rect = quit_.get_rect()
    quit_rect.x, quit_rect.y = qx, qy

    hs_font = pygame.font.Font(font_name, 25)
    hs_text = hs_font.render(f'Highscore: {highscore}', False, color1)
    hx, hy = 50, HEIGHT//10*1.5+16
    cs_text = hs_font.render(f'Your score: {score}', False, color1)
    cx, cy = 50, HEIGHT//10*1.5+48

    if not playing_menu_song:
        mixer.Channel(0).play(menu_background_song, loops=-1)
        playing_menu_song = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            
            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                if pressed[pygame.K_1]:
                    playing_menu_song = False
                    mixer.Channel(0).stop()
                    screen_animation(main)
                if pressed[pygame.K_2]:
                    screen_animation(start_menu)
                if pressed[pygame.K_3]:
                    quit_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = pygame.mouse.get_pressed()
                left = state[0]
                mouse_pos = pygame.mouse.get_pos()
                if left:
                    mixer.Channel(1).play(click_sound)
                    if play_rect.collidepoint(mouse_pos):
                        screen_animation(main)
                    if main_rect.collidepoint(mouse_pos):
                        screen_animation(start_menu)
                    if quit_rect.collidepoint(mouse_pos):
                        quit_game()

        mouse_pos = pygame.mouse.get_pos()

        if play_rect.collidepoint(mouse_pos):
            play_ = subtitle_font.render('Play again', False, color1)
        else:
            play_ = subtitle_font.render('Play again', False, color4)
        
        if main_rect.collidepoint(mouse_pos):
            main_ = subtitle_font.render('Main menu', False, color1)
        else:
            main_ = subtitle_font.render('Main menu', False, color4)
        
        if quit_rect.collidepoint(mouse_pos):
            quit_ = subtitle_font.render('Exit game', False, color1)
        else:
            quit_ = subtitle_font.render('Exit game', False, color4)

        DISPLAY.blit(game_over_bg, (0,0))
        DISPLAY.blit(over_, (gx, gy))
        DISPLAY.blit(play_, (px, py))
        DISPLAY.blit(main_, (mx, my))
        DISPLAY.blit(quit_, (qx, qy))
        DISPLAY.blit(hs_text, (hx, hy))
        DISPLAY.blit(cs_text, (cx, cy))
        
        draw_cursor()
        CLOCK.tick(FPS)
        pygame.display.update()

def start_menu():
    reset_mouse_pos()
    global is_drawing_cursor
    global playing_menu_song
    is_drawing_cursor = True
    play_again = False
    show_credits = False
    exit_game = False
    show_tutorial = False
    bg_image = pygame.image.load(f'{img_path}{sep}main_bg.png').convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    title_font = pygame.font.Font(font_name, 65)
    title = title_font.render('Space evasion', False, color4)
    tx, ty = 40, 40
    subtitle_font = pygame.font.Font(font_name, 35)
    tutorial_font = pygame.font.Font(font_name, 20)
    start = subtitle_font.render('Start game', False, color4)
    cred = subtitle_font.render('Credits', False, color4)
    quit_ = subtitle_font.render('Exit game', False, color4)
    tutorial_ = tutorial_font.render('Tutorial', False, color4)
    sx, sy = 50, HEIGHT//10*5
    cx, cy = 50, HEIGHT//10*6
    qx, qy = 50, HEIGHT//10*7
    tx2, ty2 = 50, HEIGHT//10*9
    start_rect = start.get_rect()
    start_rect.x, start_rect.y = sx, sy
    cred_rect = cred.get_rect()
    cred_rect.x, cred_rect.y = cx, cy
    quit_rect = quit_.get_rect()
    quit_rect.x, quit_rect.y = qx, qy
    tutorial_rect = tutorial_.get_rect()
    tutorial_rect.x, tutorial_rect.y = tx2, ty2

    hs_font = pygame.font.Font(font_name, 25)
    hs_text = hs_font.render(f'Highscore: {highscore}', False, color1)
    hx, hy = 50, HEIGHT//10*1.75

    if not playing_menu_song:
        mixer.Channel(0).play(menu_background_song, loops=-1)
        playing_menu_song = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                play_again = pressed[pygame.K_1]
                show_credits = pressed[pygame.K_2]
                exit_game = pressed[pygame.K_3]
                show_tutorial = pressed[pygame.K_4]
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = pygame.mouse.get_pressed()
                left = state[0]
                mouse_pos = pygame.mouse.get_pos()
                
                if left:
                    mixer.Channel(1).play(click_sound)
                    play_again = start_rect.collidepoint(mouse_pos)
                    show_credits = cred_rect.collidepoint(mouse_pos)
                    exit_game = quit_rect.collidepoint(mouse_pos)
                    show_tutorial = tutorial_rect.collidepoint(mouse_pos)                

        mouse_pos = pygame.mouse.get_pos()
        if start_rect.collidepoint(mouse_pos):
            start = subtitle_font.render('Start game', False, color1)
        else:
            start = subtitle_font.render('Start game', False, color4)
        
        if cred_rect.collidepoint(mouse_pos):
            cred = subtitle_font.render('Credits', False, color1)
        else:
            cred = subtitle_font.render('Credits', False, color4)
        
        if quit_rect.collidepoint(mouse_pos):
            quit_ = subtitle_font.render('Exit game', False, color1)
        else:
            quit_ = subtitle_font.render('Exit game', False, color4)
        
        if tutorial_rect.collidepoint(mouse_pos):
            tutorial_ = tutorial_font.render('Tutorial', False, color1)
        else:
            tutorial_ = tutorial_font.render('Tutorial', False, color4)

        if play_again:
            mixer.Channel(0).stop()
            playing_menu_song = False
            screen_animation(main)
        elif show_credits:
            screen_animation(credits)
        elif exit_game:
            quit_game()
        elif show_tutorial:
            screen_animation(tutorial)

        DISPLAY.blit(bg_image, (0,0))
        DISPLAY.blit(title, (tx, ty))
        DISPLAY.blit(start, (sx, sy))
        DISPLAY.blit(cred, (cx, cy))
        DISPLAY.blit(quit_, (qx, qy))
        DISPLAY.blit(tutorial_, (tx2, ty2))
        DISPLAY.blit(hs_text, (hx, hy))
        
        draw_cursor()
        CLOCK.tick(FPS)
        pygame.display.update()

def credits():
    reset_mouse_pos()
    global is_drawing_cursor
    is_drawing_cursor = True
    main_menu, play_game, exit_game = False, False, False

    background = pygame.image.load(f'{img_path}{sep}main_bg.png').convert_alpha()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    bg_overlay = pygame.image.load(f'{img_path}{sep}credit_overlay.png').convert_alpha()
    bg_overlay = pygame.transform.scale(bg_overlay, (WIDTH, HEIGHT))

    title_font = pygame.font.Font(font_name, 65)
    subtitle_font = pygame.font.Font(font_name, 30)

    ctext = title_font.render('Credits', False, color4)
    cx, cy = 40, 40

    button_font = pygame.font.Font(font_name, 35)

    main_menu_text = button_font.render('Go back', False, color4)
    mmtw, mmth = button_font.size('Go back')
    mmtx = WIDTH-mmtw-30
    mmty = HEIGHT-mmth-30
    main_menu_rect = main_menu_text.get_rect()
    main_menu_rect.x, main_menu_rect.y = mmtx, mmty
    
    texts = [
        'Game Programmer: Nemo Eriksson',
        'Art: Nemo Eriksson',
        'Sound FX: Nemo Eriksson',
        'Music: ',
        ' - "Diablo II LoD title theme": Blizzard',
        ' - "Beginning 2": c418',
        '',
        'Space Evasion 2021 All right reserved',
    ]

    iteration = 100
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            
            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()

                main_menu = pressed[pygame.K_1]
                play_game = pressed[pygame.K_2]
                exit_game = pressed[pygame.K_3]
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = pygame.mouse.get_pressed()
                if state[0]:
                    mixer.Channel(1).play(click_sound)

                    mouse_pos = pygame.mouse.get_pos()
                    if main_menu_rect.collidepoint(mouse_pos):
                        screen_animation(start_menu)

        if main_menu:
            screen_animation(start_menu)
        elif play_game:
            screen_animation(main)
        elif exit_game:
            quit_game()

        DISPLAY.blit(background, (0,0))

        for index, text in enumerate(texts):
            text = subtitle_font.render(text, False, color4)
            y = WIDTH//10*(8)+index*48 - iteration
            DISPLAY.blit(text, (50, y))
            if index == len(texts)-1 and y <= 150:
                screen_animation(start_menu)
            
        mouse_pos = pygame.mouse.get_pos()
        if main_menu_rect.collidepoint(mouse_pos):
            main_menu_text = button_font.render('Go back', False, color1)
        else:
            main_menu_text = button_font.render('Go back', False, color4)

        DISPLAY.blit(bg_overlay, (0,0))
        DISPLAY.blit(ctext, (cx, cy))
        DISPLAY.blit(main_menu_text, (mmtx, mmty))

        iteration += 30/FPS
        CLOCK.tick(FPS)
        draw_cursor()
        pygame.display.update()

tmp = pygame.image.load(f'{img_path}{sep}warning_laser.png').convert_alpha()
tmp = pygame.transform.rotate(tmp, 90)
for i in range((WIDTH-11*16)//16):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_game()   
    x = (i+5)*16
    DISPLAY.blit(tmp, (x, HEIGHT//10*8))
    pygame.display.update()
    CLOCK.tick(FPS*1.5)

start_menu()
