import pygame
import random
import mido  # MIDI library
import math

SUBFRAMES = 1
SPEED = 0.125
BALL_CT = 34
SLOMO = 0.5
GRAVITY = 0.5

_speed = SPEED
NOTE_VEL_MULT = 4.5
last_note_time = 0  # Time when the last note was played
dampening_level = 0  # Current dampening level
velocity = 127

GRID_ROWS = 24
GRID_COLS = 14

key_intervals = {
    pygame.K_q: -7,
    pygame.K_w: +7,
    pygame.K_a: -5,
    pygame.K_s: +5,
    pygame.K_z: -2,
    pygame.K_x: +2,
    pygame.K_e: -1,
    pygame.K_r: +1,
    pygame.K_d: -12,
    pygame.K_f: +12
}

scales = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'pentatonic': [0, 2, 4, 7, 9],
    'blues': [0, 3, 5, 6, 7, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
    'double_harmonic': [0, 1, 4, 5, 7, 8, 11],
    'enigmatic': [0, 1, 4, 6, 8, 10, 11],
    'hungarian_minor': [0, 2, 3, 6, 7, 8, 11],
    'persian': [0, 1, 4, 5, 6, 8, 11],
    'hirajoshi': [0, 2, 3, 7, 8],
    'iwato': [0, 1, 5, 6, 10],
    'neapolitan_major': [0, 1, 3, 5, 7, 9, 11],
    'neapolitan_minor': [0, 1, 3, 5, 7, 8, 11],
    'octatonic': [0, 1, 3, 4, 6, 7, 9, 10],
    'whole_tone': [0, 2, 4, 6, 8, 10],
    
}

chords = {
    'major_seventh': [0, 4, 7, 11, 12, 16, 19, 23],      # Major seventh chord
    'minor_seventh': [0, 3, 7, 10, 12, 15, 19, 22],      # Minor seventh chord
    #'half_diminished': [0, 3, 6, 10, 12, 15, 18, 22],    # Half-diminished seventh chord
    #'diminished_seventh': [0, 3, 6, 9, 12, 15, 18, 21],  # Diminished seventh chord
    'added_ninth': [0, 4, 7, 14, 12, 16, 19, 26],        # Added ninth chord
    'sixth': [0, 4, 7, 9, 12, 16, 19, 21],               # Sixth chord
    #'minor_sixth': [0, 3, 7, 9, 12, 15, 19, 21],         # Minor sixth chord
    #'ninth': [0, 4, 7, 10, 14, 12, 16, 19, 23, 26],      # Ninth chord
    'minor_ninth': [0, 3, 7, 10, 14, 12, 15, 19, 22, 26],# Minor ninth chord
    #'eleventh': [0, 4, 7, 10, 14, 17, 12, 16, 19, 22, 26], # Eleventh chord
    #'thirteenth': [0, 4, 7, 10, 14, 17, 21, 12, 16, 19, 22, 26], # Thirteenth chord
}

current_scale = chords['major_seventh']
#name, current_scale = random.choice(list(chords.items()))
root_note = 60

# Load MIDI file and extract notes
#midi_file = mido.MidiFile('canonpiano.mid')
port = mido.open_output('BallsMidi 1')  # Open a MIDI output port
# Process MIDI file and group notes by their timestamps
from collections import defaultdict
midi_notes_grouped_by_time = defaultdict(list)
current_time = 0
# for msg in midi_file:
#     if not msg.is_meta:
#         current_time += msg.time
#         if msg.type == 'note_on':
#             midi_notes_grouped_by_time[current_time].append(msg.note)

note_times = sorted(midi_notes_grouped_by_time.keys())
current_note_time_index = 0



def play_midi_note(ball, speedoption = 0):
    global last_note_time
    if speedoption < 0:
        speedoption *= -1

    velocity = min(int(speedoption * NOTE_VEL_MULT), 127)

    # Calculate panning based on ball position
    panning = int((ball.pos[0] / width) * 127)
    panning = max(0, min(127, panning))  # Clamp value between 0 and 127

    scale_note = random.choice(current_scale)

    last_note_time = pygame.time.get_ticks()
    midi_note = root_note + scale_note
    port.send(mido.Message('control_change', control=10, value=panning))
    port.send(mido.Message('note_on', note=midi_note, velocity=velocity))
    port.send(mido.Message('note_off', note=midi_note, velocity=velocity))


def assign_ball_to_grid(ball):
    col = int(ball.pos[0] / grid_cell_width)
    row = int(ball.pos[1] / grid_cell_height)
    if ball not in grid[row][col]:
        grid[row][col].append(ball)

def update_ball_in_grid(ball, old_pos):
    # Remove from old cell
    old_col = int(old_pos[0] / grid_cell_width)
    old_row = int(old_pos[1] / grid_cell_height)
    if ball in grid[old_row][old_col]:
        grid[old_row][old_col].remove(ball)
    

    # Add to new cell
    assign_ball_to_grid(ball)

def draw_grid():
    # Draw vertical lines for columns
    for col in range(1, GRID_COLS):
        pygame.draw.line(screen, gray, (col * grid_cell_width, 0), (col * grid_cell_width, height))

    # Draw horizontal lines for rows
    for row in range(1, GRID_ROWS):
        pygame.draw.line(screen, gray, (0, row * grid_cell_height), (width, row * grid_cell_height))


# Initialize Pygame and MIDI
pygame.init()


# Window settings
width, height = 405,720  # 9:16 aspect ratio
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Ball with MIDI")


grid_cell_width = width / GRID_COLS
grid_cell_height = height / GRID_ROWS
grid = [[[] for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]




# Colors
black = (0, 0, 0)
white = (255, 255, 255)
gray = (77, 77, 77)

import colorsys
def generate_color():
    hue = random.choice((0,0.1,0.3,0.6,0.7,0.8))

    # High saturation: 80% to 100%
    saturation = 1

    # High value: 80% to 100%
    value = 1

    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

    # Convert RGB from 0-1 range to 0-255 range and make them integers
    r, g, b = int(r * 255), int(g * 255), int(b * 255)

    return r, g, b

ball_positions = [(x, y) for x in range(8) for y in range(15)]


class Ball:
    def __init__(self):
        self.radius = 10
        self.color = generate_color()
        self.pos = random.choice(ball_positions)
        ball_positions.remove(self.pos)
        scaled_x = self.pos[0] * 45 + 45  # Example scaling
        scaled_y = self.pos[1] * 45 + 45  # Example scaling with boundary check
        self.pos = [scaled_x, scaled_y]
        velocity_magnitude = 5  # You can adjust this value as needed
        

        # Random angle in radians
        angle = random.uniform(0, 2 * math.pi)

        # Calculate velocity components
        self.vel = [velocity_magnitude * math.cos(angle), velocity_magnitude * math.sin(angle)]
        self.gravity = GRAVITY

    def move(self):
        
        # Update position and velocity
        for _ in range(SUBFRAMES):  # Subframe calculation for smoother ball movement
            old_pos = self.pos.copy()
            update_ball_in_grid(self, old_pos)

            self.vel[1] += self.gravity / SUBFRAMES * _speed
            self.pos[0] += self.vel[0] / SUBFRAMES * _speed
            self.pos[1] += self.vel[1] / SUBFRAMES * _speed

        # Check for collision with frame and adjust
        if self.pos[0] - self.radius <= margin + frame_thickness or self.pos[0] + self.radius >= width - margin - frame_thickness:
            self.vel[0] *= -1
            self.pos[0] = max(margin + frame_thickness + self.radius, min(width - margin - frame_thickness - self.radius, self.pos[0]))
            play_midi_note(self, self.vel[0])
            #self.color = generate_color()

        if self.pos[1] - self.radius <= margin + frame_thickness or self.pos[1] + self.radius >= height - margin - frame_thickness:
            self.vel[1] *= -1
            self.pos[1] = max(margin + frame_thickness + self.radius, min(height - margin - frame_thickness - self.radius, self.pos[1]))
            play_midi_note(self, self.vel[1])
            #self.color = generate_color()
        
        assign_ball_to_grid(self)




    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

def collide(ball1, ball2, max_attempts=10):


    # Calculate direction vector between ball centers
    dx = ball1.pos[0] - ball2.pos[0]
    dy = ball1.pos[1] - ball2.pos[1]

    # Calculate distance between balls
    distance = (dx**2 + dy**2)**0.5
    if distance == 0:
        return  # Avoid division by zero

    # Normalize the direction vector
    dx /= distance
    dy /= distance

    # Calculate velocity components along the direction vector
    velocity1 = dx*ball1.vel[0] + dy*ball1.vel[1]
    velocity2 = dx*ball2.vel[0] + dy*ball2.vel[1]

    # Swap the velocity components for an elastic collision
    ball1.vel[0] += (velocity2 - velocity1) * dx
    ball1.vel[1] += (velocity2 - velocity1) * dy
    ball2.vel[0] += (velocity1 - velocity2) * dx
    ball2.vel[1] += (velocity1 - velocity2) * dy
    # Play a note on collision
    relative_velocity = [ball2.vel[0] - ball1.vel[0], ball2.vel[1] - ball1.vel[1]]

    # Calculate the magnitude of the relative velocity (collision speed)
    collision_speed = math.sqrt(relative_velocity[0] ** 2 + relative_velocity[1] ** 2)

    attempts = 0
    while attempts < max_attempts:
        # Calculate new positions and check for overlap
        dx = ball1.pos[0] - ball2.pos[0]
        dy = ball1.pos[1] - ball2.pos[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance >= ball1.radius * 2:
            play_midi_note(ball1, collision_speed)
            break  # Balls are no longer overlapping

        # Adjust positions to resolve overlap
        overlap = (ball1.radius * 2) - distance
        adjust_x = dx * overlap / distance / 2
        adjust_y = dy * overlap / distance / 2
        ball1.pos[0] += adjust_x
        ball1.pos[1] += adjust_y
        ball2.pos[0] -= adjust_x
        ball2.pos[1] -= adjust_y

        attempts += 1


    #ball1.color = generate_color()
    #ball2.color = generate_color()
    # Pass collision speed to play_midi_note() along with the ball object
    

def balls_collide(ball1, ball2):
        distance = ((ball1.pos[0] - ball2.pos[0]) ** 2 + (ball1.pos[1] - ball2.pos[1]) ** 2) ** 0.5
        return distance < ball1.radius * 2


# Frame settings
frame_thickness = 10
margin = 10

# Function to draw frames
def draw_frames():
    pygame.draw.rect(screen, white, [margin, margin, width - 2*margin, height - 2*margin], frame_thickness)
    # Uncomment below to draw the alternate circular frame
    # pygame.draw.circle(screen, white, (width//2, height//2), (width - 2*margin)//2, frame_thickness)


balls = [Ball() for x in range(BALL_CT)]  # Start with one ball




# Example: When initializing balls
for ball in balls:
    assign_ball_to_grid(ball)


# Main loop
# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in key_intervals:
                root_note += key_intervals[event.key]
                root_note = max(0, min(root_note, 127)) 
            if event.key == pygame.K_SPACE:
                if current_scale == chords['major_seventh']:
                    current_scale = chords['minor_seventh']
                elif current_scale == chords['minor_seventh']:
                    current_scale = chords['minor_ninth']
                else:
                    current_scale = chords['major_seventh']
            if event.key == pygame.K_1:
                if _speed == SPEED:
                    _speed = SLOMO * SPEED
                else:
                    _speed = SPEED



        # Add event handling to spawn new balls if needed
        # Example: if event.type == YOUR_CHOSEN_EVENT:
        #             balls.append(Ball())
    #compressor_eval()
    # In your main loop
    for ball in balls:
        col = int(ball.pos[0] / grid_cell_width)
        row = int(ball.pos[1] / grid_cell_height)

        # Check adjacent cells including the current cell
        for adj_row in range(max(0, row - 1), min(GRID_ROWS, row + 2)):
            for adj_col in range(max(0, col - 1), min(GRID_COLS, col + 2)):
                for other_ball in grid[adj_row][adj_col]:
                    if ball is not other_ball and balls_collide(ball, other_ball):
                        collide(ball, other_ball)


    # Move and draw each ball
    screen.fill(black)
    draw_frames()
    #draw_grid()
    #draw_compressor_line(velocity)
    for ball in balls:
        ball.move()
        ball.draw()

    pygame.display.flip()
    pygame.time.Clock().tick(60)  # 60 FPS

# Clean up
pygame.quit()
port.close()
