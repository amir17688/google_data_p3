# -*- coding: utf-8 -*-

# Copyright (c) 2010-2015 Tuukka Turto
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
AI routines for skeletons
"""

from pyherc.ai.pathfinding import a_star
from pyherc.aspects import log_debug
from pyherc.data.geometry import find_direction
from pyherc.data import find_free_space
from pyherc.events import new_lose_focus_event, new_notice_event
from pyherc.ports import is_move_legal, move, attack, equip


class SkeletonWarriorAI():
    """
    AI for skeleton warrior

    ..versionadded:: 0.7
    """
    @log_debug
    def __init__(self, character):
        """
        Default constructor

        :param character: character to connect
        :type character: Character
        """
        self.character = character

        self.mode = 'patrol'
        self.destination = None

    def __call__(self, model, action_factory, rng):
        self.act(model, action_factory, rng)

    @log_debug
    def act(self, model, action_factory, rng):
        """
        Trigger this AI to assess the situation and act accordingly

        :param model: model where the character is located
        :type model: Model
        :param action_factory: factory to create actions
        :type action_factory: ActionFactory
        :param rng: random number generator
        :type rng: Random
        """
        del self.character.short_term_memory[:]

        if self.character.inventory.weapon is None:
            self._wield_weapon(action_factory)

        c_location = self.character.location
        p_location = model.player.location

        distance = ((c_location[0] - p_location[0]) ** 2 +
                    (c_location[1] - p_location[1]) ** 2) ** 0.5

        if distance < 4:
            if self.mode != 'combat':
                self.character.raise_event(
                                    new_notice_event(character = self.character,
                                                     target = model.player))
            self.mode = 'combat'
        else:
            if self.mode != 'patrol':
                self.character.raise_event(
                                new_lose_focus_event(character = self.character))
            self.mode = 'patrol'

        if self.mode == 'patrol':
            self._patrol(model, action_factory, rng)
        else:
            self._combat(model, action_factory, rng)

    @log_debug
    def _wield_weapon(self, action_factory):
        """
        Check if it is possible to wield a weapon and do so
        """
        weapons = [item for item in
                   self.character.inventory
                   if item.weapon_data is not None]

        if weapons:
            equip(self.character,
                  weapons[0])

    @log_debug
    def _patrol(self, model, action_factory, rng):
        """
        Patrol around the level
        """
        character = self.character
        level = self.character.level

        while (self.destination is None
               or character.location == self.destination):

            self.destination = find_free_space(level)

        path, connections, updated = a_star(character.location,
                                            self.destination,
                                            level)

        next_tile = path[1]

        direction = find_direction(character.location,
                                   next_tile)

        if is_move_legal(character,
                         direction,
                         'walk',
                         action_factory):
            move(character, direction, action_factory)
        else:
            character.tick = character.tick + 10

    @log_debug
    def _combat(self, model, action_factory, rng):
        """
        Attack enemies
        """
        character = self.character
        player = model.player
        c_location = character.location
        p_location = player.location

        distance = ((c_location[0] - p_location[0]) ** 2 +
                    (c_location[1] - p_location[1]) ** 2) ** 0.5

        if distance == 1:
            direction = find_direction(c_location,
                                       p_location)
            attack(character,
                   direction,
                   rng)
        else:
            path, connections, updated = a_star(c_location,
                                                p_location,
                                                character.level)
            next_tile = path[1]

            direction = find_direction(character.location,
                                       next_tile)

            if is_move_legal(character,
                             direction,
                             'walk',
                             action_factory):
                move(character, direction, action_factory)
            else:
                character.tick = character.tick + 10
