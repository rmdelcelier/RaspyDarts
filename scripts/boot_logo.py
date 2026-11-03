"""
Images of the boot screen (Plymouth, scripts/install_on_pi.sh) : the logo of RaspyDarts and the
light behind it, which pulses while the Raspberry Pi starts (as if lit from behind).

    python scripts/boot_logo.py <logo RGBA>

Writes images/boot_logo.png (the logo, LOGO_WIDTH pixels wide on a 1920 x 1080 screen),
images/boot_halo.png (the light : the shape of the logo widened and blurred, warm white near
it, red further away ; HALO_MARGIN pixels around the logo), placed one over the other, and
images/boot_background.png (the screen behind them : black).
"""

import sys

from PIL import Image, ImageChops, ImageFilter

LOGO_WIDTH = 1000
HALO_MARGIN = 150
# (widened by, blurred by, colour, strength) : from the red far away to the warm white near
LAYERS = ((31, 70, (255, 60, 20), 1.6), (15, 28, (255, 170, 90), 1.4), (7, 10, (255, 240, 210), 1.2))


def main(source):
    logo = Image.open(source).convert('RGBA')
    logo = logo.crop(logo.getbbox())
    logo = logo.resize((LOGO_WIDTH, round(logo.height * LOGO_WIDTH / logo.width)), Image.LANCZOS)
    logo.save('images/boot_logo.png', optimize=True)

    size = (logo.width + 2 * HALO_MARGIN, logo.height + 2 * HALO_MARGIN)
    shape = Image.new('L', size, 0)
    shape.paste(logo.getchannel('A'), (HALO_MARGIN, HALO_MARGIN))
    halo = Image.new('RGBA', size, (0, 0, 0, 0))
    for widen, blur, colour, strength in LAYERS:
        alpha = shape.filter(ImageFilter.MaxFilter(widen)).filter(ImageFilter.GaussianBlur(blur))
        alpha = alpha.point(lambda value, strength=strength: min(255, int(value * strength)))
        layer = Image.new('RGBA', size, colour + (0,))
        layer.putalpha(alpha)
        halo = Image.alpha_composite(halo, layer)
    # Nothing under the logo itself : the light only shows around it
    halo.putalpha(ImageChops.multiply(halo.getchannel('A'), ImageChops.invert(
        shape.filter(ImageFilter.MinFilter(5)))))
    halo.save('images/boot_halo.png', optimize=True)
    Image.new('RGB', (1920, 1080), (0, 0, 0)).save('images/boot_background.png', optimize=True)
    print(f"logo {logo.size}, halo {halo.size}")


if __name__ == '__main__':
    main(sys.argv[1])
