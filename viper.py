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
import pygame
import pygcurse
import random
import sys

from pygame.locals import (K_SPACE, K_UP, K_LEFT, K_DOWN, K_RIGHT, K_ESCAPE,
                           KEYDOWN, QUIT)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

LEVEL = 'level.ini'


class Game:
    def __init__(self, clock):
        self.clock = clock
        self.level = Level(LEVEL)
        self.player = Player(LEVEL)
        self.current_number = 0

        # Setting the position of the number on the player ensures that a new
        # number will be generated.
        self.number_pos = self.player.head()
        self.is_paused = False

        self.win = pygcurse.PygcurseWindow(self.level.width,
                                           self.level.height,
                                           'Viper')
        self.draw_state()
        self.new_number()

    def change_pause(self):
        if self.is_paused:
            self.draw_state()
            self.is_paused = False
        else:
            self.is_paused = True
            region = (self.level.width // 2 - 13,
                      self.level.height // 2 - 2,
                      26,
                      3)
            pause = pygcurse.PygcurseTextbox(self.win,
                                             region=region,
                                             fgcolor=self.level.text_color,
                                             bgcolor=self.level.box_color,
                                             text='Press space to continue!')
            pause.update()
            self.win.update()

    def draw_state(self):
        # Draw the level
        self.win.fill(' ', bgcolor=self.level.background_color)
        for i in range(self.level.width):
            for j in range(self.level.height):
                if self.level.grid[i][j]:
                    self.win.putchar(' ',
                                     x=i,
                                     y=j,
                                     bgcolor=self.level.boundary_color)

        # Draw the number
        self.win.cursor = self.number_pos
        self.win.putchar(str(self.current_number),
                         fgcolor=self.level.text_color,
                         bgcolor=self.level.background_color)

        # Draw the player
        for point in self.player.position:
            self.win.cursor = point
            self.win.putchar(' ', bgcolor=self.level.player_color)

    def game_over(self):
        region = (self.level.width // 2 - 6,
                  self.level.height // 2 - 2,
                  12,
                  3)
        end = pygcurse.PygcurseTextbox(self.win,
                                       region=region,
                                       fgcolor=self.level.text_color,
                                       bgcolor=self.level.box_color,
                                       text='Game Over!')
        end.update()
        self.win.update()
        pygcurse.waitforkeypress()
        pygame.quit()
        sys.exit()

    def hit_number(self):
        return (self.level.collision(self.number_pos) or
                self.player.collision(self.number_pos))

    def death(self):
        return (self.level.collision(self.player.head()) or
                self.player.collision(self.player.head(), skip_head=True))

    def loop(self):
        event = pygame.event.poll()

        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == K_SPACE:
                self.change_pause()

            if self.is_paused:
                return
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

        self.next_frame()
        self.clock.tick_busy_loop(self.player.speed)

    def next_frame(self):
        if self.is_paused:
            return

        old_tail = self.player.move()
        self.level.warp_player_head(self.player)
        if self.death():
            self.game_over()

        self.win.cursor = self.player.head()
        self.win.putchar(' ', bgcolor=self.level.player_color)

        if old_tail is not None:
            self.win.putchar(' ',
                             x=old_tail[0],
                             y=old_tail[1],
                             bgcolor=self.level.background_color)

        if self.hit_number():
            self.new_number()

    def new_number(self):
        self.player.grow()
        self.current_number += 1

        while self.hit_number():
            self.number_pos = (random.randint(0, self.level.width - 1),
                               random.randint(0, self.level.height - 1))

        self.win.cursor = self.number_pos
        self.win.putchar(str(self.current_number % 10),
                         fgcolor=self.level.text_color,
                         bgcolor=self.level.background_color)


class Level:
    def __init__(self, filename):
        # Load the configuration file
        config = configparser.ConfigParser()
        config.read(filename)
        self.player_color = pygame.Color(config['Colors']['Player'])
        self.boundary_color = pygame.Color(config['Colors']['Boundary'])
        self.background_color = pygame.Color(config['Colors']['Background'])
        self.text_color = pygame.Color(config['Colors']['Text'])
        self.box_color = pygame.Color(config['Colors']['Box'])
        self.width = int(config['Dimensions']['Width'])
        self.height = int(config['Dimensions']['Height'])

        # Create the grid where True is an obstacle and False is empty
        self.grid = []
        for i in range(self.width):
            self.grid.append([False] * self.height)
        # for i in range(self.width):
        #     self.grid[i][0] = True
        #     self.grid[i][-1] = True
        # for j in range(self.height):
        #     self.grid[0][j] = True
        #     self.grid[-1][j] = True

    def collision(self, coordinate):
        """Checks whether the coordinate is a wall."""
        return self.grid[coordinate[0]][coordinate[1]]

    def warp_player_head(self, player):
        """Puts the player head back into the level if it went outside."""
        player.position[-1] = (player.position[-1][0] % self.width,
                               player.position[-1][1] % self.height)


class Player:
    def __init__(self, filename):
        # Load the configuration file
        config = configparser.ConfigParser()
        config.read(filename)
        self.growth = int(config['Player']['Growth'])
        self.speed = int(config['Player']['Speed'])
        self.to_grow = 0

        self.direction = config['Player']['Direction']
        if self.direction == 'up':
            self.direction = UP
        elif self.direction == 'down':
            self.direction = DOWN
        elif self.direction == 'left':
            self.direction = LEFT
        elif self.direction == 'right':
            self.direction = RIGHT

        height = int(config['Dimensions']['Height'])
        width = int(config['Dimensions']['Width'])
        startx = int(config['Player']['Startx']) % width
        starty = int(config['Player']['Starty']) % height

        # This array will contain all coordinates occupied by the player
        self.position = [(startx, starty)]

    def collision(self, coordinate, skip_head=False):
        """Checks whether the player occupies the coordinate. If skip_head is
        True, then it skips checking the coordinate of the head."""
        if skip_head:
            return coordinate in self.position[:-1]
        else:
            return coordinate in self.position

    def grow(self):
        self.to_grow += self.growth

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

    def tail(self):
        """Returns the coordinate of the tail of the player."""
        return self.position[0]

    def shrink(self):
        """Removes the tail of the player."""
        del self.position[0]


if __name__ == "__main__":
    pygame.init()
    game = Game(pygame.time.Clock())
    while 1:
        game.loop()
