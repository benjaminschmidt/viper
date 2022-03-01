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

CONFIG = 'level.ini'


class Game:
    def __init__(self, clock):
        self.clock = clock

        # Load the configuration file
        config = configparser.ConfigParser()
        config.read(CONFIG)
        self.player_color = pygame.Color(config['Colors']['Player'])
        self.boundary_color = pygame.Color(config['Colors']['Boundary'])
        self.background_color = pygame.Color(config['Colors']['Background'])
        self.text_color = pygame.Color(config['Colors']['Text'])
        self.box_color = pygame.Color(config['Colors']['Box'])
        self.height = int(config['Level']['Height'])
        self.width = int(config['Level']['Width'])
        self.growth = int(config['Level']['Growth'])
        self.speed = int(config['Level']['Speed'])

        # Create the grid where True is an obstacle and False is empty
        self.grid = []
        for i in range(self.width):
            self.grid.append([False]*self.height)
        for i in range(self.width):
            self.grid[i][0] = True
            self.grid[i][-1] = True
        for j in range(self.height):
            self.grid[0][j] = True
            self.grid[-1][j] = True

        # This array will contain all coordinates occupied by the player
        self.player_pos = [(self.width // 2, self.height // 2)]

        self.player_direction = RIGHT
        self.player_length = 1
        self.to_grow = 0
        self.current_number = 0
        self.is_paused = False

        # Setting the position of the number on the player ensures that a new
        # number will be generated.
        self.number_pos = self.player_pos[-1]

        self.win = pygcurse.PygcurseWindow(self.width, self.height, 'Viper')
        self.draw_state()
        self.new_number()

    def change_pause(self):
        if self.is_paused:
            self.draw_state()
            self.is_paused = False
        else:
            self.is_paused = True
            pause = pygcurse.PygcurseTextbox(self.win,
                                             region=(self.width // 2 - 13,
                                                     self.height // 2 - 2,
                                                     26,
                                                     3),
                                             fgcolor=self.text_color,
                                             bgcolor=self.box_color,
                                             text='Press space to continue!')
            pause.update()
            self.win.update()

    def draw_state(self):
        # Draw the level
        self.win.fill(' ', bgcolor=self.background_color)
        for i in range(self.width):
            for j in range(self.height):
                if self.grid[i][j]:
                    self.win.putchar(' ',
                                     x=i,
                                     y=j,
                                     bgcolor=self.boundary_color)

        # Draw the number
        self.win.cursor = self.number_pos
        self.win.putchar(str(self.current_number),
                         fgcolor=self.text_color,
                         bgcolor=self.background_color)

        # Draw the player
        for point in self.player_pos:
            self.win.cursor = point
            self.win.putchar(' ', bgcolor=self.player_color)

    def game_over(self):
        end = pygcurse.PygcurseTextbox(self.win,
                                       region=(self.width // 2 - 6,
                                               self.height // 2 - 2,
                                               12,
                                               3),
                                       fgcolor=self.text_color,
                                       bgcolor=self.box_color,
                                       text='Game Over!')
        end.update()
        self.win.update()
        pygcurse.waitforkeypress()
        pygame.quit()
        sys.exit()

    def hit_number(self):
        return (self.grid[self.number_pos[0]][self.number_pos[1]] or
                self.number_pos in self.player_pos)

    def hit_wall(self):
        x = self.player_pos[-1][0]
        y = self.player_pos[-1][1]
        if self.grid[x][y]:
            return True
        elif self.player_pos[-1] in self.player_pos[:-1]:
            return True
        else:
            return False

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
                if self.player_direction != DOWN:
                    self.player_direction = UP
            elif event.key == K_DOWN:
                if self.player_direction != UP:
                    self.player_direction = DOWN
            elif event.key == K_LEFT:
                if self.player_direction != RIGHT:
                    self.player_direction = LEFT
            elif event.key == K_RIGHT:
                if self.player_direction != LEFT:
                    self.player_direction = RIGHT

        self.next_frame()
        self.clock.tick_busy_loop(self.speed)

    def next_frame(self):
        if self.is_paused:
            return

        next_pos = (self.player_pos[-1][0] + self.player_direction[0],
                    self.player_pos[-1][1] + self.player_direction[1])
        self.player_pos.append(next_pos)
        if self.hit_wall():
            self.game_over()

        self.win.cursor = next_pos
        self.win.putchar(' ', bgcolor=self.player_color)

        if self.to_grow == 0:
            self.win.cursor = self.player_pos[0]
            self.win.putchar(' ', bgcolor=self.background_color)
            del self.player_pos[0]
        else:
            self.to_grow -= 1

        if self.hit_number():
            self.new_number()

    def new_number(self):
        self.to_grow += self.growth
        self.current_number += 1

        while self.hit_number():
            self.number_pos = (random.randint(0, self.width - 1),
                               random.randint(0, self.height - 1))

        self.win.cursor = self.number_pos
        self.win.putchar(str(self.current_number % 10),
                         fgcolor=self.text_color,
                         bgcolor=self.background_color)


if __name__ == "__main__":
    pygame.init()
    game = Game(pygame.time.Clock())
    while 1:
        game.loop()
