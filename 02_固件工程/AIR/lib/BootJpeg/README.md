# Boot animation decoder

Vendored TJpgDec R0.03 by ChaN, 2021. Copyright and license terms are retained at the top of src/tjpgd.c.

Source: https://elm-chan.org/fsw/tjpgd/arc/tjpgd3.zip
Documentation: https://elm-chan.org/fsw/tjpgd/00index.html
Official patch: https://elm-chan.org/fsw/tjpgd/patches.html

Local changes: RGB565 output, scaling disabled, 32-bit fast Huffman decoding; official 2023 grayscale clipping patch; use stdint.h on modern Windows hosts too. GCC speed optimization is scoped to this decoder translation unit. No Arduino wrapper or external dependency.
