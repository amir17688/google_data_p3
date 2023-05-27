import atom
from lxml import etree


def test_element():
    e = atom.Element(name="name", text="Mark Pilgrim")
#    assert str(e) == "<name>Mark Pilgrim</name>\n"

    tree = etree.fromstring(str(e))
    assert tree.attrib == {}
    assert tree.tag == "name"
    assert tree.text == "Mark Pilgrim"
    assert (not tree.getchildren())

def test_element_with_attributes():
    e = atom.Element(name="name", text="Mark Pilgrim", age=18, sex="man")
#    assert str(e) == '<name age="18" sex="man">Mark Pilgrim</name>\n'

    tree = etree.fromstring(str(e))
    assert tree.attrib == {'age': '18', 'sex': 'man'}
    assert tree.text == "Mark Pilgrim"
    assert (not tree.getchildren())

def test_element_with_children():
    child = atom.Element(name="name", text="Mark Pilgrim")
    parent = atom.Element(name="author")
    parent.append_children(child)
#    assert str(parent) == (
#        "<author>\n"
#        "  <name>Mark Pilgrim</name>\n"
#        "</author>\n"
#    )

    tree = etree.fromstring(str(parent))
    assert tree.attrib == {}
    assert tree.tag == "author"
    assert tree.text.strip() == ""
    assert len(tree.getchildren()) == 1

    child_tree = tree.getchildren()[0]
    assert child_tree.attrib == {}
    assert child_tree.tag == "name"
    assert child_tree.text.strip() == "Mark Pilgrim"
    assert (not child_tree.getchildren())

if __name__ == "__main__":
    test_element()
    test_element_with_attributes()
    test_element_with_children()