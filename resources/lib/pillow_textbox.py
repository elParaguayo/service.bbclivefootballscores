# -*- coding: utf-8 -*-
'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

'''
    Text Box function for Pillow.
    by elParaguayo

    This is heavily based on the pygame function by David Clark:
      see: http://www.pygame.org/pcr/text_rect/index.php

    See pillow_textbox docstring for instructions.
'''
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

__all__ = ["TextBoxException", "pillow_textbox"]

VERSION = "0.1"


class TextBoxException(Exception):
    """Custom exception class for handling text box errors."""
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


def _draw_textbox(string, rect, font, text_color, background_color,
                  justification=0, vjustification=0, margin=0,
                  truncate=True, word_wrap=True):
    """
    Main function definition for rendering the text box.

    NB The user is not expected to call this method directly. Instead the user
    should call the "pillow_textbox" function.
    """

    # Set up variables to track the lines to render and the overall height
    # required to draw the text.
    final_lines = []
    final_height = 0

    # Define maximum height and width
    max_width = (rect[0] - (margin[0] + margin[1]))
    max_height = (rect[1] - (margin[2] + margin[3]))

    # Let's get the list of lines to draw.
    requested_lines = string.splitlines()

    # Loop over the text and see what can be drawn in the defined area.
    for requested_line in requested_lines:

        # Check if the line too long.
        if font.getsize(requested_line)[0] > max_width:

            # Have we disabled word wrapping?
            if not word_wrap:
                msg = ("Too Long. The line '{}' is too long "
                       "to fit in the defined area. Try setting "
                       "'word_wrap' to True to split "
                       "line.".format(requested_line))
                raise TextBoxException(msg)

            else:
                # If it is, break the line down into individual words
                words = requested_line.split(' ')

                # If any of our words are too long to fit, return.
                for word in words:
                    if font.getsize(word)[0] >= max_width:
                        msg = ("Too Long. The word '{}' is too long "
                               "to fit in the defined area.".format(word))
                        raise TextBoxException(msg)

                # Start a new line
                accumulated_line = ""

                # Loop over the words in the line and add as many as can fit
                for word in words:
                    test_line = accumulated_line + word + " "

                    # Build the line while the words fit.
                    if font.getsize(test_line.strip())[0] < max_width:

                        # if the word fits on the line, add it to our main line
                        accumulated_line = test_line

                    else:
                        # if it doesn't add the main line to our list
                        final_lines.append(accumulated_line)

                        # record the height of the new line
                        final_height += font.getsize(accumulated_line)[1]

                        # and add the word to the start of a new line.
                        accumulated_line = word + " "

                # make sure we catch the last line
                final_lines.append(accumulated_line)
                final_height += font.getsize(accumulated_line)[1]

        else:
            # Line is short enough so it can be added straightaway.
            final_lines.append(requested_line)
            final_height += font.getsize(requested_line)[1]

    # Let's check the height of the rendered text now.
    # If it's too tall...
    if final_height >= max_height:

        # If user has said we can't truncate text then we raise an exception
        if not truncate:
            msg = ("Once word-wrapped, the text was too tall to fit "
                   "in the defined area.")
            raise TextBoxException(msg)

        # If we can truncate, we need to work out where...
        else:

            # Define a list to store the lines that we can draw
            txt_to_draw = []

            # Track the height required for the text.
            draw_height = 0

            # Loop over the lines...
            for line in final_lines:

                # Add the height of the line to our running total
                draw_height += font.getsize(line)[1]

                # If we've not exceeded our limit...
                if draw_height <= max_height:

                    # ... the line is good to draw
                    txt_to_draw.append(line)

                # If not...
                else:

                    # ...then we can't add any more lines, so let's exit
                    # the loop.
                    break

    # No height issue here
    else:
        txt_to_draw = final_lines


    # Time to start drawing the text

    # Define a couple of images:
    #   "full_textbox": the final image
    #   "textbox":      a smaller textbox just holding the text (this is then
    #                   positioned on "full_textbox" based on the vertical
    #                   alignment required.)
    full_textbox = Image.new("RGBA", rect, color=background_color)
    textbox = Image.new("RGBA", (rect[0], final_height), color=background_color)

    # We need to be able to draw text on "textbox" so create a Draw instance
    draw = ImageDraw.Draw(textbox)

    # We need to track the height of each line so we know how to position the
    # next one
    accumulated_height = 0

    # Loop over the lines
    for line in txt_to_draw:

        # Get the size of the line
        linesize = font.getsize(line.strip())

        # Layout based on horizontal alignment

        # Left aligned
        if justification == 0:
            # pos = (0 + margin[0], accumulated_height), font.getsize(line.strip())
            pos = (0 + margin[0], accumulated_height)
            draw.text(pos,
                      line.strip(),
                      text_color,
                      font=font)

        # Centered
        elif justification == 1:
            pos = ((rect[0] - linesize[0]) / 2, accumulated_height)
            draw.text(pos,
                      line.strip(),
                      text_color,
                      font=font)

        # Right aligned
        elif justification == 2:
            pos = (rect[0] - linesize[0] - margin[1], accumulated_height)
            draw.text(pos,
                      line.strip(),
                      text_color,
                      font=font)

        # If we're here then the user has done something a bit silly...
        # We should let them know.
        else:
            msg = ("Invalid horizontal justification argument: {}. "
                   "Valid arguments are 0, 1 or 2.").format(justification)
            raise TextBoxException(msg)

        # Keep tracking the height
        accumulated_height += linesize[1]


    # Vertical alignment time...

    # Top alignment
    if vjustification == 0:
        vpos = (0, margin[2])
        full_textbox.paste(textbox, vpos)

    # Middle alignment
    elif vjustification == 1:
        vpos = (0, ((rect[1] - accumulated_height)/2))
        full_textbox.paste(textbox, vpos)

    # Bottom alignment
    elif vjustification == 2:
        vpos = (0, (rect[1] - accumulated_height - margin[3]))
        full_textbox.paste(textbox, vpos)

    # Again, we shouldn't be here....
    else:
        msg = ("Invalid vertical justification argument: {}. "
               "Valid arguments are 0, 1 or 2.").format(vjustification)
        raise TextBoxException(msg)

    # Done!
    # Send the text box back.
    return full_textbox

def pillow_textbox(string, rect, text_color=(255,255,255),
                   background_color=(0,0,0), font=None,
                   justification=0, vjustification=0, margin=0,
                   autofit=False, font_path=None, max_font=20, min_font=8,
                   truncate=False, word_wrap=True):
    """
    Returns an image containing the passed text string, reformatted
    to fit within the given area, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:
      string:           The text you wish to render. \n begins a new line.
                        Can render unicode accented characters (depending on the
                        font used).
      rect:             A tuple giving the size of the output image
                          e.g. (height, width)
      text_color:       A tuple of the rgb value of the text color.
                          e.g. (0, 0, 0) --> black
      background_color: A tuple of the rgb value of the background.
                          e.g. (255, 255, 255) --> white
      justification:    An integer to choose horizontal alignment:
                          0: (default) left-justified
                          1: horizontally centered
                          2: right-justified
      vjustification:   An integer to choose vertical alignment:
                          0: (default) top aligned
                          1: middle alignment
                          2: bottom aligned
      margin:           Defines the margin to be applied to the text box. Takes
                        a tuple (left, right, top, bottom). Several options
                        available:
                          margin=5 --> (5, 5, 5, 5)
                          margin=(5, 10) --> (5, 5, 10, 10)
                          Default 0.
      autofit:          Setting this to true will try to autofit text within
                        the image area by reducing the font size. The size range
                        can be defined by setting the max_font and min_font
                        parameters. If text still does not fit when minimum font
                        size is reached then the text will be truncated.
                        Default False.
      font_path:        Path to a True Type font. This must be set if using the
                        autofit option otherwise an exception will be raised.
                        This can also be used instead of the "font" parameter.
      max_font:         Defines the maximum font size to be used when
                        autofitting. Also defines font size if no ImageFont
                        object passed for normal rendering. Default 20.
      min_font:         Defines the minimum font size to be used when
                        autofitting. Default 8.
      truncate:         Truncates text if it doesn't fit in the defined area
                        instead of raising error. Default False.
      word_wrap:        Allows lines to wrap in given text area. Default True.

    Returns an Image in with the dimensions matching those passes as the "rect"
    parameter.
    """
    # Start off with some error checking

    # Horizontal alignment check
    if justification not in [0, 1, 2]:
        msg = ("Invalid horizontal justification argument: {}. "
               "Valid arguments are 0, 1 or 2.").format(justification)
        raise TextBoxException(msg)

    # Vertical alignment check
    if vjustification not in [0, 1, 2]:
        msg = ("Invalid vertical justification argument: {}. "
               "Valid arguments are 0, 1 or 2.").format(vjustification)
        raise TextBoxException(msg)

    # Font check
    if font is None:
        if font_path is None:
            msg = ("No font defined. You must provide an ImageFont object or "
                   "provide the name of a TrueType font")
            raise TextBoxException(msg)

        else:
            try:
                font = ImageFont.truetype(font_path, size=max_font)
            except:
                msg("Unable to create ImageFont object from 'name': '{}' and "
                    "'size': {}.").format(font_path, max_font)
                raise TextBoxException(msg)


    if autofit and font_path is None:
        msg = "You must set the 'font_path' parameter when using 'autofit'."
        raise TextBoxException(msg)

    # Font size check
    if type(max_font) is not int or type(min_font) is not int:
        msg = "Invalid font size. Size value must be an integer."
        raise TextBoxException(msg)

    if min_font < 1 or max_font < 1:
        msg = "Invalid font size. Size cannot be less than 1."
        raise TextBoxException(msg)

    # Define margins
    if type(margin) is tuple:
        if not all(isinstance(x, int) for x in margin) or len(margin) not in [2, 4]:
            msg = "Invalid margin definition '{}'.".format(margin)
            raise TextBoxException(msg)

        if len(margin) == 2:
            margin = (margin[0], margin[0], margin[1], margin[1])

    elif type(margin) is int:
        margin = (margin, margin, margin, margin)

    else:
        msg = "Invalid margin definition '{}'.".format(margin)
        raise TextBoxException(msg)

    # Ready to go now

    # If we're not autofitting the text then we just need one go at this
    if not autofit:
        surface = _draw_textbox(string, rect,
                                font, text_color, background_color,
                                justification=justification,
                                vjustification=vjustification,
                                margin=margin, truncate=truncate,
                                word_wrap=word_wrap)

    # If we are autofitting text...
    else:

        # ... prepare variables for our loop
        fontsize = max_font
        fit = False

        # Loop over font sizes (starting at the largest) until we find the size
        # where the text fits
        while fontsize >= min_font:

            # Create the ImageFont object
            myfont = ImageFont.truetype(font_path, size=fontsize)

            # Let's see if it fits
            try:
                textbox = _draw_textbox(string, rect,
                                        myfont, text_color, background_color,
                                        justification=justification,
                                        vjustification=vjustification,
                                        margin=margin, truncate=False,
                                        word_wrap=word_wrap)

                # It fits. Exit the loop.
                fit = True
                break

            # Text is too big so let's reduce the font size and try again.
            except:
                fontsize -= 1

        # If we didn't find a fit within our loop then will truncate the text.
        if not fit:
            textbox = _draw_textbox(string, rect,
                                    myfont, text_color, background_color,
                                    justification=justification,
                                    vjustification=vjustification,
                                    margin=margin, truncate=True,
                                    word_wrap=word_wrap)

    return textbox
