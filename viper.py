r"""
Remake of the classic game snake.
"""

# ****************************************************************************
#       Copyright (C) 2022 Benjamin Schmidt <schmbe@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ****************************************************************************

import configparser
import os
import pygame
import pygcurse
import random
import sys

from pygame.locals import (K_SPACE, K_UP, K_LEFT, K_DOWN, K_RIGHT,
                           K_n, K_y, KEYDOWN, QUIT)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


def absolute_coordinate(coordinate):
    """Takes a coordinate on the level and returns the corresponding
    coordinate on the window."""
    return coordinate[0], coordinate[1] + 1


class Game:
    def __init__(self, clock):
        self.clock = clock

        config = configparser.ConfigParser()
        config.read('settings.ini')

        self.player_color = pygame.Color(config['Colors']['Player'])
        self.boundary_color = pygame.Color(config['Colors']['Boundary'])
        self.background_color = pygame.Color(config['Colors']['Background'])
        self.text_color = pygame.Color(config['Colors']['Text'])
        self.box_color = pygame.Color(config['Colors']['Box'])

        self.width = int(config['Campaign']['Width'])
        self.height = int(config['Campaign']['Height'])
        self.initial_lives = int(config['Campaign']['Lives'])
        self.levelmask = config['Campaign']['Levelmask']
        self.current_level = 0

        self.number_pos = (0, 0)
        self.current_number = 0

        # Will later contain the instance of the current level.
        self.level = None
        # Will later contain the instance of the player.
        self.player = None

        # Has the game been paused via the space bar?
        self.paused = False
        # Has the player won the game?
        self.won = False
        # False means that the game is not running for any reason including
        # pause, game over, or won.
        self.running = True

        # This will be the set to the coordinates of a box on the screen later.
        self.box_region = None

        self.win = pygcurse.PygcurseWindow(*self.window_dimensions(), 'Viper')
        self.next_level()

    def next_level(self):
        self.current_level += 1
        filename = self.levelmask.replace('*', str(self.current_level))
        if not os.path.exists(filename):
            self.won = True
            self.draw_box('You won! Play again? y/n')
            return
        self.level = Level(filename, self.width, self.height)
        if self.player is None:
            self.player = Player(self.level, self.initial_lives)
        else:
            self.player = Player(self.level, self.player.lives)

        self.current_number = 0

        # Setting the position of the number on the player ensures that a new
        # number will be generated.
        self.number_pos = self.player.head()

        self.paused = False
        self.won = False
        self.running = True

        self.box_region = None

        print(self.window_dimensions())
        self.win.resize(*self.window_dimensions())

        self.draw_game()
        self.new_number()
        self.change_pause()

    def restart_game(self):
        self.current_level = 0
        self.player = None
        self.next_level()

    def change_pause(self):
        if self.paused:
            self.draw_game()
            self.paused = False
            self.running = True
        else:
            self.paused = True
            self.running = False
            self.draw_box('Press space to play!')

    def new_number(self):
        self.player.grow()
        self.current_number += 1

        while self.hit_number():
            self.number_pos = (random.randint(0, self.level.width - 1),
                               random.randint(0, self.level.height - 1))

        self.draw_number()
        self.draw_info()

    def loop(self):
        event = pygame.event.poll()

        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if self.player.lives == 0 or self.won:
                if event.key == K_n:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_y:
                    self.restart_game()
            elif event.key == K_SPACE:
                self.change_pause()
            elif self.paused:
                pass
            elif event.key == K_UP:
                if self.player.direction != DOWN:
                    self.player.direction = UP
            elif event.key == K_DOWN:
                if self.player.direction != UP:
                    self.player.direction = DOWN
            elif event.key == K_LEFT:
                if self.player.direction != RIGHT:
                    self.player.direction = LEFT
            elif event.key == K_RIGHT:
                if self.player.direction != LEFT:
                    self.player.direction = RIGHT

        if self.running:
            self.next_frame()
        self.clock.tick_busy_loop(self.level.speed)

    def next_frame(self):
        old_tail = self.player.move()
        self.player.warp_player_head()
        if self.is_dead():
            self.death()
            return

        self.win.cursor = absolute_coordinate(self.player.head())
        self.win.putchar(' ', bgcolor=self.player_color)

        if old_tail is not None:
            self.win.cursor = absolute_coordinate(old_tail)
            self.win.putchar(' ', bgcolor=self.background_color)

        if self.hit_number():
            if self.current_number == self.level.goal:
                self.current_number += 1
                self.draw_info()
                self.running = False
                self.next_level()
                return
            self.new_number()

    def delete_player(self):
        for point in self.player.position:
            if self.level.grid[point[0]][point[1]]:
                self.win.cursor = absolute_coordinate(point)
                self.win.putchar(' ', bgcolor=self.boundary_color)
            else:
                self.win.cursor = absolute_coordinate(point)
                self.win.putchar(' ', bgcolor=self.background_color)

    def draw_box(self, text):
        self.box_region = (self.level.width // 2 - len(text) // 2 - 1,
                           self.level.height // 2 - 2,
                           len(text) + 2,
                           3)
        box = pygcurse.PygcurseTextbox(self.win,
                                       region=self.box_region,
                                       fgcolor=self.text_color,
                                       bgcolor=self.box_color,
                                       text=text)
        box.update()
        self.win.update()

    def draw_game(self):
        self.draw_level()
        self.draw_number()
        self.draw_player()
        self.draw_info()

    def draw_level(self):
        if self.box_region is None:
            x = 0
            y = 0
            width = self.level.width
            height = self.level.height
        else:
            x, y, width, height = self.box_region

        self.win.fill(bgcolor=self.background_color,
                      region=self.box_region)
        for i in range(x, x + width):
            for j in range(y, y + height):
                if self.level.grid[i][j]:
                    self.win.cursor = absolute_coordinate((i, j))
                    self.win.putchar(' ',
                                     x=i,
                                     y=j + 1,
                                     bgcolor=self.boundary_color)

    def draw_number(self):
        self.win.cursor = absolute_coordinate(self.number_pos)
        self.win.putchar(str(self.current_number % 10),
                         fgcolor=self.text_color,
                         bgcolor=self.background_color)

    def draw_player(self):
        if self.box_region is None:
            x = 0
            y = 0
            width = self.level.width
            height = self.level.height
        else:
            x, y, width, height = self.box_region

        # Draw the player
        for point in self.player.position:
            if x <= point[0] < x + width and y <= point[1] < y + height:
                self.win.cursor = absolute_coordinate(point)
                self.win.putchar(' ', bgcolor=self.player_color)

    def draw_info(self):
        width, height = self.window_dimensions()
        self.win.fill(bgcolor=self.background_color,
                      region=(0, 0, width, 1))
        self.win.cursor = (0, 0)
        self.win.putchars(('Score: ' + str(self.current_number - 1)
                           + '/' + str(self.level.goal)),
                          fgcolor=self.text_color,
                          bgcolor=self.background_color)
        self.win.cursor = (width - 10, 0)
        self.win.putchars('Lives: ' + str(self.player.lives),
                          fgcolor=self.text_color,
                          bgcolor=self.background_color)

    def death(self):
        self.running = False
        if self.player.lives == 1:
            self.player.lives -= 1
            self.draw_box('Game Over! Play again? y/n')
        else:
            self.reset_player()

    def hit_number(self):
        return (self.level.collision(self.number_pos) or
                self.player.collision(self.number_pos))

    def is_dead(self):
        return (self.level.collision(self.player.head()) or
                self.player.collision(self.player.head(), skip_head=True))

    def reset_player(self):
        self.delete_player()
        self.player.next_life()

        self.running = True

        self.current_number = 0

        # Setting the position of the number on the player ensures that a new
        # number will be generated.
        self.number_pos = self.player.head()

        # This will be the set to the coordinates of a box on the screen later.
        self.box_region = None

        self.draw_game()
        self.new_number()
        self.change_pause()

    def window_dimensions(self):
        return self.width, self.height + 1


class Level:
    def __init__(self, filename, width, height):
        # Load the configuration file
        config = configparser.ConfigParser()
        config.read(filename)

        self.width = width
        self.height = height

        self.goal = int(config['Level']['Goal'])

        self.initial_direction = config['Level']['Direction']
        if self.initial_direction == 'up':
            self.initial_direction = UP
        elif self.initial_direction == 'down':
            self.initial_direction = DOWN
        elif self.initial_direction == 'left':
            self.initial_direction = LEFT
        elif self.initial_direction == 'right':
            self.initial_direction = RIGHT

        self.growth = int(config['Level']['Growth'])
        self.speed = int(config['Level']['Speed'])
        self.initial_position = (int(config['Level']['Initialx']),
                                 int(config['Level']['Initialy']))

        # Create the grid where True is an obstacle and False is empty
        self.grid = []
        # Initialize the grid with no walls.
        for i in range(self.width):
            self.grid.append([False] * self.height)

        for line in config['Obstacle Lines'].values():
            x_0, y_0, x_1, y_1 = (int(element) for element in line.split(','))
            self.add_line((x_0, y_0), (x_1, y_1))

    def collision(self, coordinate):
        """Checks whether the coordinate is a wall."""
        return self.grid[coordinate[0]][coordinate[1]]

    def add_line(self, start, end):
        """Adds a line of obstacles from start to end.
        We use Bresenham's algorithm."""
        slope_steep = abs(end[1] - start[1]) > abs(end[0] - start[0])
        if slope_steep:
            if start[1] > end[1]:
                # We draw in increasing y-direction.
                start, end = end, start
            # We do the same algorithm as for flat slope,
            # but with x and y exchanged.
            x = start[1]
            y = start[0]
            dx = end[1] - start[1]
            dy = end[0] - start[0]
        else:
            if start[0] > end[0]:
                # For a flat slope, we draw in increasing x-direction
                start, end = end, start
            x = start[0]
            y = start[1]
            dx = end[0] - start[0]
            dy = end[1] - start[1]

        if dy >= 0:
            slope_sign = 1
        else:
            slope_sign = -1

        decision = slope_sign * 2 * dy - dx
        for i in range(dx + 1):
            if slope_steep:
                self.grid[y][x] = True
            else:
                self.grid[x][y] = True
            x += 1
            if decision > 0:
                y += slope_sign
                decision += slope_sign * 2 * dy - 2 * dx
            else:
                decision += slope_sign * 2 * dy


class Player:
    def __init__(self, level, lives):
        self.level = level
        self.lives = lives
        self.direction = self.level.initial_direction
        self.position = self.level.initial_position

        # How much should the player grow until it stops.
        self.to_grow = 0

        # This array will contain all coordinates occupied by the player
        self.position = [self.level.initial_position]

    def collision(self, coordinate, skip_head=False):
        """Checks whether the player occupies the coordinate. If skip_head is
        True, then it skips checking the coordinate of the head."""
        if skip_head:
            return coordinate in self.position[:-1]
        else:
            return coordinate in self.position

    def grow(self):
        self.to_grow += self.level.growth

    def head(self):
        """Returns the coordinate of the head of the player."""
        return self.position[-1]

    def move(self):
        """Moves the player by one frame and returns the coordinate
        that the tail moved out of. If the snake is growing, it returns
        None."""
        next_pos = (self.head()[0] + self.direction[0],
                    self.head()[1] + self.direction[1])
        self.position.append(next_pos)

        if self.to_grow == 0:
            old_tail = self.tail()
            self.shrink()
            return old_tail
        else:
            self.to_grow -= 1
            return None

    def next_life(self):
        self.direction = self.level.initial_direction
        self.lives -= 1
        self.position = [self.level.initial_position]
        self.to_grow = 0

    def tail(self):
        """Returns the coordinate of the tail of the player."""
        return self.position[0]

    def shrink(self):
        """Removes the tail of the player."""
        del self.position[0]

    def warp_player_head(self):
        """Puts the player head back into the level if it went outside."""
        self.position[-1] = (self.position[-1][0] % self.level.width,
                             self.position[-1][1] % self.level.height)


if __name__ == "__main__":
    pygame.init()
    game = Game(pygame.time.Clock())
    while True:
        game.loop()
