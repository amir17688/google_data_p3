import atom
from lxml import etree


def test_entry():
    e_link = atom.Element(name="link", href="http://example.org/2003/12/13/atom03")
    entry = atom.Entry(title="Atom-Powered Robots Run Amok",
                       link = e_link,
                       id="urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a",
                       updated="2003-12-13T18:30:02Z",
                       summary="Some text.")
#    assert str(entry) == (
#        "<entry>\n"
#        "  <summary>Some text.</summary>\n"
#        "  <updated>2003-12-13T18:30:02Z</updated>\n"
#        "  <link href=\"http://example.org/2003/12/13/atom03\"/>\n"
#        "  <title>Atom-Powered Robots Run Amok</title>\n"
#        "  <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>\n"
#        "</entry>\n"
#        )

    tree = etree.fromstring(str(entry))
    assert tree.attrib == {}
    assert tree.tag == "entry"
    assert not tree.text.strip()
    assert len(tree.getchildren()) == 5

    e_summary = tree.xpath("/entry/summary")[0]
    assert e_summary.attrib == {}
    assert e_summary.tag == "summary"
    assert e_summary.text.strip() == "Some text."

    e_updated = tree.xpath("/entry/updated")[0]
    assert e_updated.attrib == {}
    assert e_updated.tag == "updated"
    assert e_updated.text.strip() == "2003-12-13T18:30:02Z"

    e_link = tree.xpath("/entry/link")[0]
    assert e_link.attrib == {'href' : "http://example.org/2003/12/13/atom03"}
    assert e_link.tag == "link"
    assert not e_link.text


if __name__ == "__main__":
    test_entry()