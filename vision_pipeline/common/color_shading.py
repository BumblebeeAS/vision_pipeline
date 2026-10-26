"""GStreamer filters for camera color balance and lens shading."""

import math


def color_shading_filter(coefficients):
    """Build an RGBA filter for fitted log(R/G) and log(B/G) surfaces.

    Coordinates range from -1 to 1, with (-1, -1) at the image's top left.
    Coefficient order is 1, x, y, x*x, x*y, y*y, (x*x + y*y)**2.
    """
    terms = ("1.0", "x", "y", "x*x", "x*y", "y*y", "r2*r2")
    expressions = []
    for channel in ("red", "blue"):
        values = [float(value) for value in coefficients[channel]]
        if len(values) != len(terms) or any(
            not math.isfinite(value) or abs(value) > 2 for value in values
        ):
            raise ValueError(
                f"Expected seven finite shading coefficients within [-2, 2] for {channel}"
            )
        expressions.append("+".join(
            f"({value:.9f})*({term})" for value, term in zip(values, terms)
        ))
    # Clamp extrapolation beyond the calibrated paper area. The common scale
    # preserves the luminance of a neutral surface while removing its color cast.
    shader = (
        "precision highp float; varying vec2 v_texcoord; uniform sampler2D tex; "
        "void main(){vec4 color=texture2D(tex,v_texcoord);"
        "float x=2.0*v_texcoord.x-1.0;float y=2.0*v_texcoord.y-1.0;"
        "float r2=x*x+y*y;"
        f"vec2 ratio=exp(clamp(vec2({expressions[0]},{expressions[1]}),"
        "vec2(-0.5),vec2(0.7)));"
        "float scale=dot(vec3(ratio.x,1.0,ratio.y),vec3(0.2126,0.7152,0.0722));"
        "gl_FragColor=vec4(color.rgb*scale/vec3(ratio.x,1.0,ratio.y),color.a);}"
    )
    return (
        f'glupload ! glshader fragment="{shader}" ! '
        "gldownload ! video/x-raw,format=RGBA ! "
    )


def color_correction_filter(rgb_gains=None, shading=None):
    """Build color conversion, RGB balance, and optional shading correction."""
    color_format = "RGBA" if rgb_gains is not None or shading is not None else "BGRx"
    color_conversion = f"nvvidconv ! video/x-raw,format={color_format} ! "
    if rgb_gains is not None:
        if len(rgb_gains) != 3 or any(
            not math.isfinite(float(gain)) or not 0.3333 <= float(gain) <= 3.0
            for gain in rgb_gains
        ):
            raise ValueError("Expected three RGB gains between 0.3333 and 3")
        # frei0r's multiply controls map 0..1 logarithmically to 0.3333..3.
        controls = [
            math.log(float(gain) / 0.3333) / math.log(3.0 / 0.3333)
            for gain in rgb_gains
        ]
        color_conversion += (
            "frei0r-filter-coloradj-rgb action=1 keep-luma=false "
            f"r={controls[0]:.8f} g={controls[1]:.8f} b={controls[2]:.8f} ! "
        )
    if shading is not None:
        color_conversion += color_shading_filter(shading)

    return color_conversion
