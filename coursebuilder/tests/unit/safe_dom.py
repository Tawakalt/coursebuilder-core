"""Unit tests for the common.sanitize module."""

__author__ = 'John Orr (jorr@google.com)'

import unittest
from common import safe_dom


class MockNode(safe_dom.Node):
    def __init__(self, value):
        self._value = value

    @property
    def sanitized(self):
        return self._value


class NodeListTests(unittest.TestCase):
    """Unit tests for common.safe_dom.NodeList."""

    def test_list(self):
        """NodeList should escape all its members."""
        node_list = safe_dom.NodeList()
        node_list.append(MockNode('a')).append(MockNode('b'))
        self.assertEqual('ab', node_list.sanitized)


class TextTests(unittest.TestCase):
    """Unit tests for common.safe_dom.Text."""

    def test_text_sanitizes(self):
        """Text should sanitize unsafe characters."""
        unsafe_string = '<script>'
        text = safe_dom.Text(unsafe_string)
        self.assertEqual('&lt;script&gt;', text.sanitized)

    def test_str_returns_sanitized(self):
        """The _str__ method should return sanitized text."""
        unsafe_string = '<script>'
        text = safe_dom.Text(unsafe_string)
        self.assertEqual('&lt;script&gt;', text.__str__())


class ElementTests(unittest.TestCase):
    """Unit tests for common.safe_dom.Element."""

    def test_build_simple_element(self):
        """Element should build an element without attributes or children."""
        element = safe_dom.Element('p')
        self.assertEqual('<p></p>', element.__str__())

    def test_reject_bad_tag_names(self):
        """Element should reject non-alphabetical tag names."""
        bad_names = ['a2', 'a b', '@', 'a-b']
        for name in bad_names:
            try:
                safe_dom.Element(name)
            except AssertionError:
                continue
            self.fail('Expected an exception: "%s"' % name)

    def test_reject_bad_attribute_names(self):
        """Element should reject non-alphabetical attribute names."""
        bad_names = ['a2', 'a b', '@', 'a-b']
        for name in bad_names:
            try:
                safe_dom.Element('p', **{name: 'good value'})
            except AssertionError:
                continue
            self.fail('Expected an exception: "%s"' % name)

    def test_include_attributes(self):
        """Element should include tag attributes."""
        element = safe_dom.Element('button', style='foo', onclick='action')
        self.assertEqual(
            '<button style="foo" onclick="action"></button>',
            element.__str__())

    def test_escape_quotes(self):
        """Element should escape single and double quote characters."""
        element = safe_dom.Element('a', href='a\'b"c')
        self.assertEqual('<a href="a%27b%22c"></a>', element.__str__())

    def test_allow_parens(self):
        """Element should allow parentheses in attributes."""
        element = safe_dom.Element('a', action='myAction()')
        self.assertEqual('<a action="myAction()"></a>', element.__str__())

    def test_allow_urls(self):
        """Element should allow urls with a method sepcified in an attribute."""
        url = 'http://a.b.com/d/e/f?var1=val1&var2=val2#fragment'
        element = safe_dom.Element('a', action=url)
        self.assertEqual('<a action="%s"></a>' % url, element.__str__())

    def test_allow_url_query_chars(self):
        """Element should pass '?', '=', and '&' characters in an attribute."""
        element = safe_dom.Element('a', action='target?action=foo&value=bar')
        self.assertEqual(
            '<a action="target?action=foo&value=bar"></a>', element.__str__())

    def test_convert_none_to_empty(self):
        """An attribute with value None should render as empty."""
        element = safe_dom.Element('a', action=None)
        self.assertEqual('<a action=""></a>', element.__str__())

    def test_coerce_className(self):  # pylint: disable-msg=g-bad-name
        """Element should replace the 'className' attrib with 'class'."""
        element = safe_dom.Element('p', className='foo')
        self.assertEqual('<p class="foo"></p>', element.__str__())

    def test_include_children(self):
        """Element should include child elements."""
        element = safe_dom.Element('a').add_child(
            safe_dom.Element('b').add_child(
                safe_dom.Element('c'))
        ).add_child(
            safe_dom.Element('d'))
        self.assertEqual('<a><b><c></c></b><d></d></a>', element.__str__())

    def test_sanitize_children(self):
        """Element should sanitize child elements as they are included."""
        element = safe_dom.Element('td').add_child(
            safe_dom.Element('a', href='foo"bar').add_text('1<2'))
        self.assertEqual(
            '<td><a href="foo%22bar">1&lt;2</a></td>', element.__str__())


class EntityTest(unittest.TestCase):
    """Unit tests for common.safe_dom.Entity."""

    def expect_pass(self, test_text):
        entity = safe_dom.Entity(test_text)
        self.assertEqual(test_text, entity.__str__())

    def expect_fail(self, test_text):
        try:
            safe_dom.Entity(test_text)
        except AssertionError:
            return
        self.fail('Expected an assert exception')

    def test_should_pass_named_entities(self):
        self.expect_pass('&nbsp;')

    def test_should_pass_decimal_entities(self):
        self.expect_pass('&#38;')

    def test_should_pass_hex_entities(self):
        self.expect_pass('&#x26AB;')

    def test_entities_must_start_with_ampersand(self):
        self.expect_fail('nbsp;')

    def test_entities_must_end_with_semicolon(self):
        self.expect_fail('&nbsp')

    def test_named_entities_must_be_all_alpha(self):
        self.expect_fail('&qu2ot;')

    def test_decimal_entities_must_be_all_decimal_digits(self):
        self.expect_fail('&#12A6;')

    def test_hex_entities_must_be_all_hex_digits(self):
        self.expect_fail('&#x26AG')

    def test_entitiesmust_be_non_empty(self):
        self.expect_fail('&;')
        self.expect_fail('&#;')
        self.expect_fail('&#x;')

    def test_should_reject_extraneous_characters(self):
        self.expect_fail(' &nbsp;')
        self.expect_fail('&nbsp; ')

    def test_should_reject_tampering(self):
        entity = safe_dom.Entity('&nbsp;')
        entity._entity = '<script/>'
        try:
            entity.__str__()
        except AssertionError:
            return
        self.fail('Expected an assert exception')

