import pygame


def change_colour(image, colour, special_flags=pygame.BLEND_MULT):
    colouredImage = pygame.Surface(image.get_size())
    colouredImage.fill(colour)

    finalImage = image.copy()
    finalImage.blit(colouredImage, (0, 0), special_flags=special_flags)
    return finalImage
