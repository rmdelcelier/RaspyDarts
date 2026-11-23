"""
The font of the game, for the screens drawn without the Screen (the trophies) : the Screen gives
it (include/cscreen.py, use_chosen_font)
"""
import pygame

path = None


def font(size, bold=False):    # pylint: disable=unused-argument
    '''
    The font of the game at this size. bold : kept for the callers, not applied : the bold made by
    pygame (set_bold) thickens the strokes of the font of the theme until it is not recognised
    (CompactaBT, condensed : Trophées et progression looked written in another font)
    '''
    return pygame.font.Font(path, int(size))
