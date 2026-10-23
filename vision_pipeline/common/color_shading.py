"""GStreamer correction for smooth, lens-dependent color shading."""

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
