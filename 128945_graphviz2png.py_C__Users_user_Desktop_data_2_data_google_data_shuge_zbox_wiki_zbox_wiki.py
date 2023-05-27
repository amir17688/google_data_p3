#!/usr/bin/env python
"""
This script requires

 * PyGraphviz (python-pygraphviz on Ubuntu)

References

  - Trac Graphviz Plugin
"""
import os
import pygraphviz

__all__ = [
    "dot_text2png",
    "dot_file2png",
]


def dot_text2png(text, png_path, prog = "dot"):
    """ generate a image/png file from 'text' and write into 'png_path'.  """
    text = text.strip()
    filename = str(hash(text)).replace("-", "")
    fullname = filename + ".png"

    if os.path.isdir(png_path):
        save_to_prefix = png_path
    else:
        save_to_prefix = os.path.dirname(png_path)

    png_path = os.path.join(save_to_prefix, fullname)

    if os.path.exists(png_path):
        return png_path

#    print "generating ..."

    g = pygraphviz.AGraph(text)
    g.layout(prog = prog)
    g.draw(png_path)

    return png_path


def dot_file2png(dot_path, png_path):
    """ generate a image/png file from 'dot_path' and write into 'png_path'.  """
    text = file(dot_path).read()

    return dot_text2png(text = text, png_path = png_path)


test_text = """digraph G {
    rankdir = "LR"

    GraphvizPlugin[ URL = GraphvizPlugin ]

    ZBoxWiki[
      URL = "http://wiki.shuge-lab.org"
      fontcolor = red
    ]

    GraphvizPlugin -> ZBoxWiki
}
"""

if __name__ == "__main__":
    save_to_prefix = "/tmp/zbox_wiki_graphviz_demo"
    if not os.path.exists(save_to_prefix):
        os.makedirs(save_to_prefix)

    png_path = save_to_prefix
    png_path = "/tmp/zbox_wiki_graphviz_demo/9071973128666914760.png"
    dst_path = dot_text2png(test_text, png_path)

    msg = "save to: " + dst_path
    print msg

