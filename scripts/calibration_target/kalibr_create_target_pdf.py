#!/usr/bin/python3
# Adapted from https://github.com/ethz-asl/kalibr/blob/master/aslam_offline_calibration/kalibr/python/kalibr_create_target_pdf
# Thomas Schneider, Sept 2013
# Codes from AprilTags C++ Library (http://people.csail.mit.edu/kaess/apriltags/)

import argparse
import math
import sys

import numpy as np
from april_tag_codes import AprilTagCodes
from pyx import canvas, color, path, style, unit


# borderBits must be consistent with the variable "blackBorder" in the detector code in file ethz_apriltag2/src/TagFamily.cc
def generateAprilTag(
    canvas,
    position,
    metricSize,
    tagSpacing,
    tagID,
    tagFamilyData,
    rotation=2,
    symmCorners=True,
    borderBits=2,
):
    # get the tag code
    try:
        tagCode = tagFamilyData.tagCodes[tagID]
    except:
        print(
            "[ERROR]: Requested tag ID of {0} not available in the {1} TagFamily".format(
                tagID, tagFamilyData.chosenTagFamily
            )
        )

    # calculate the bit size of the tag
    sqrtBits = math.sqrt(tagFamilyData.totalBits)
    bitSquareSize = metricSize / (sqrtBits + borderBits * 2)

    # position of tag
    xPos = position[0]
    yPos = position[1]

    # borders (2x bit size)
    borderSize = borderBits * bitSquareSize

    c.fill(path.rect(xPos, yPos, metricSize, borderSize), [color.rgb.black])  # bottom
    c.fill(
        path.rect(xPos, yPos + metricSize - borderSize, metricSize, borderSize),
        [color.rgb.black],
    )  # top
    c.fill(
        path.rect(xPos + metricSize - borderSize, yPos, borderSize, metricSize),
        [color.rgb.black],
    )  # left
    c.fill(path.rect(xPos, yPos, borderSize, metricSize), [color.rgb.black])  # right

    # create numpy matrix of code
    codeMatrix = np.zeros((int(sqrtBits), int(sqrtBits)))
    for i in range(0, int(sqrtBits)):
        for j in range(0, int(sqrtBits)):
            if not tagCode & (1 << int(sqrtBits) * i + j):
                codeMatrix[i, j] = 1

    # rotation
    codeMatrix = np.rot90(codeMatrix, rotation)

    # bits
    for i in range(0, int(sqrtBits)):
        for j in range(0, int(sqrtBits)):
            if codeMatrix[i, j]:
                c.fill(
                    path.rect(
                        xPos + (j + borderBits) * bitSquareSize,
                        yPos + ((borderBits - 1) + sqrtBits - i) * bitSquareSize,
                        bitSquareSize,
                        bitSquareSize,
                    ),
                    [color.rgb.black],
                )

    # add squares to make corners symmetric (decreases the effect of motion blur in the subpix refinement...)
    if symmCorners:
        metricSquareSize = tagSpacing * metricSize

        corners = [
            [xPos - metricSquareSize, yPos - metricSquareSize],
            [xPos + metricSize, yPos - metricSquareSize],
            [xPos + metricSize, yPos + metricSize],
            [xPos - metricSquareSize, yPos + metricSize],
        ]

        for point in corners:
            c.fill(
                path.rect(point[0], point[1], metricSquareSize, metricSquareSize),
                [color.rgb.black],
            )


# tagSpacing in % of tagSize
def generateAprilBoard(
    canvas,
    n_cols,
    n_rows,
    tagSize,
    border_width,
    tagSpacing=0.25,
    tagFamily="t36h11",
    skip_ids=[],
):

    if tagSpacing < 0 or tagSpacing > 1.0:
        print("[ERROR]: Invalid tagSpacing specified.  [0-1.0] of tagSize")
        sys.exit(0)

    # convert to cm
    tagSize = tagSize * 100.0
    border_width = border_width * 100.0

    # get the tag family data
    tagFamilyData = AprilTagCodes(tagFamily)

    # draw tags
    for y in range(0, n_rows):
        for x in range(0, n_cols):
            id = n_cols * y + x
            if id not in skip_ids:
                pos = (x * (1 + tagSpacing) * tagSize, y * (1 + tagSpacing) * tagSize)
                generateAprilTag(
                    canvas, pos, tagSize, tagSpacing, id, tagFamilyData, rotation=2
                )

    # Add white border padding
    board_width = n_cols * (1 + tagSpacing) * tagSize
    board_height = n_rows * (1 + tagSpacing) * tagSize

    # Draw a white border around the board
    tag_spacing_size = tagSpacing * tagSize
    c.stroke(
        path.rect(
            -border_width * 0.5 - tag_spacing_size,
            -border_width * 0.5 - tag_spacing_size,
            board_width + border_width + tag_spacing_size,
            board_height + border_width + tag_spacing_size,
        ),
        [color.rgb.white, style.linewidth(border_width)],
    )

    # Print canvas/board dimensions
    bbox = c.bbox()
    bbox.enlarge(border_width / 2)  # bbox doesn't include linewidths
    width_m = unit.tom(bbox.width())
    height_m = unit.tom(bbox.height())
    print(f"Total size with border: {width_m}m x {height_m}m")


def generateCheckerboard(canvas, n_cols, n_rows, size_cols, size_rows):
    # convert to cm
    size_cols = size_cols * 100.0
    size_rows = size_rows * 100.0

    # message
    print(
        "Generating a checkerboard with {0}x{1} corners and a box size of {2}x{3} cm".format(
            n_cols, n_rows, size_cols, size_rows
        )
    )

    # draw boxes
    for x in range(0, n_cols + 1):
        for y in range(0, n_rows + 1):
            up_left_x = x * size_cols
            up_left_y = y * size_rows
            if (x + y + 1) % 2 != 0:
                c.fill(
                    path.rect(up_left_x, up_left_y, size_cols, size_rows),
                    [color.rgb.black],
                )

    # print caption
    caption = "{0}x{1}@{2}x{3}cm".format(n_cols, n_rows, size_cols, size_rows)

    # text.preamble(r"\DeclareFixedFont{\LittleFont}{T1}{ptm}{b}{it}{0.75in}") #
    c.text(1.05 * size_cols, 0.04 * size_rows, caption)


if __name__ == "__main__":
    usage = """
    Example Aprilgrid:
        kalibr_create_target_pdf --type apriltag --nx 6 --ny 6 --tsize 0.08 --tspace 0.3
    Example Checkerboard:
        kalibr_create_target_pdf --type checkerboard --nx 6 --ny 6 -csx 0.05 --csy 0.1
    """

    # setup the argument list
    parser = argparse.ArgumentParser(
        description="Generate PDFs of calibration patterns.", usage=usage
    )

    outputOptions = parser.add_argument_group("Output options")
    outputOptions.add_argument(
        "output", nargs="?", default="target", help="Output filename"
    )
    outputOptions.add_argument(
        "--eps",
        action="store_true",
        dest="do_eps",
        help="Also output an EPS file",
        required=False,
    )

    genericOptions = parser.add_argument_group("Generic grid options")
    genericOptions.add_argument(
        "--type",
        dest="gridType",
        help="The grid pattern type. ('apriltag' or 'checkerboard')",
    )
    genericOptions.add_argument(
        "--nx",
        type=int,
        default=6,
        dest="n_cols",
        help="The number of tags in x direction (default: %(default)s)\n",
    )
    genericOptions.add_argument(
        "--ny",
        type=int,
        default=7,
        dest="n_rows",
        help="The number of tags in y direction (default: %(default)s)",
    )

    aprilOptions = parser.add_argument_group("Apriltag arguments")
    aprilOptions.add_argument(
        "--tsize",
        type=float,
        default=0.08,
        dest="tsize",
        help="The size of one tag [m] (default: %(default)s)",
    )
    aprilOptions.add_argument(
        "--tspace",
        type=float,
        default=0.3,
        dest="tagspacing",
        help="The space between the tags in fraction of the edge size [0..1] (default: %(default)s)",
    )
    aprilOptions.add_argument(
        "--borderwidth",
        type=float,
        default=0.05,
        dest="borderwidth",
        help="The width of the white border around the board [m] (default: %(default)s)",
    )
    aprilOptions.add_argument(
        "--tfam",
        default="t36h11",
        dest="tagfamily",
        help="Family of April tags {0} (default: %(default)s)".format(
            list(AprilTagCodes.TagFamilies.keys())
        ),
    )
    aprilOptions.add_argument(
        "--skip-ids",
        default="",
        dest="skipIds",
        help="Space-separated list of tag ids to leave blank (default: none)",
    )

    checkerOptions = parser.add_argument_group("Checkerboard arguments")
    checkerOptions.add_argument(
        "--csx",
        type=float,
        default=0.05,
        dest="chessSzX",
        help="The size of one chessboard square in x direction [m] (default: %(default)s)",
    )
    checkerOptions.add_argument(
        "--csy",
        type=float,
        default=0.05,
        dest="chessSzY",
        help="The size of one chessboard square in y direction [m] (default: %(default)s)",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # Parser the argument list
    try:
        parsed = parser.parse_args()
    except:
        sys.exit(0)

    # post-process arguments
    parsed.skipIds = [int(x) for x in parsed.skipIds.split(" ") if x]

    # open a new canvas
    c = canvas.canvas()

    # draw the board
    if parsed.gridType == "apriltag":
        generateAprilBoard(
            canvas,
            parsed.n_cols,
            parsed.n_rows,
            parsed.tsize,
            parsed.borderwidth,
            parsed.tagspacing,
            parsed.tagfamily,
            parsed.skipIds,
        )
    elif parsed.gridType == "checkerboard":
        generateCheckerboard(
            c, parsed.n_cols, parsed.n_rows, parsed.chessSzX, parsed.chessSzY
        )
    else:
        print("[ERROR]: Unknown grid pattern")
        sys.exit(0)

    # write to file
    c.writePDFfile(parsed.output)

    if parsed.do_eps:
        c.writeEPSfile(parsed.output)
