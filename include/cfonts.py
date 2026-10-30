"""
The font of the game, for the screens drawn without the Screen (the trophies) : the Screen gives
it (include/cscreen.py, use_chosen_font)
"""
import pygame

path = None


def font(size, bold=False):
    '''
    The font of the game at this size
    '''
    chosen = pygame.font.Font(path, int(size))
    chosen.set_bold(bold)
    return chosen
